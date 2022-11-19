"""
Implements the :class:`FileSourceZip` class which allows iterating files from a
zip archive
"""

from __future__ import annotations

import hashlib
import io
from threading import RLock
import zipfile

from scistag.filestag import FileStag
from scistag.filestag.file_source import FileSource, FileListEntry
from scistag.filestag.file_source_iterator import FileSourceIterator


class FileSourceZip(FileSource):
    """
    FileSource implementation for processing zip archives, either stored locally
    in the cloud.

    All you have to do is to provide a zip file's filename, a bytes object of a
    zipfile or an already opened zip archive and you can easily iterate through
    all files or files of a certain type via

    ``for cur_file in FileSourceZip("MyZipFile", mask="*.png"): ...``
    """

    def __init__(self, source: str | bytes | zipfile.ZipFile, **params):
        """
        :param source: The data source. Either a string (pointing to a filename,
            an URl or another FileStag compatible protocol), the data of a zip
            archive or an already opened archive.
        :param params: Additional parameters.
            See :class:`~scistag.filestag.file_source.FileSource` for the full
            parameter list supported by FileSources.
        """
        super().__init__(**params)
        self.source_filename = ""
        "The name of the source file"
        self.source_identifier = ""
        "The unique identifier"
        self.source_data: bytes | None = None
        "The source data stream"
        if isinstance(source, str):  # local file
            self.source_filename = source
            self.source_identifier = source
            if FileStag.is_simple(source):
                source = zipfile.ZipFile(source, "r")
            else:  # from repo or from the web
                data_stream = io.BytesIO(FileStag.load(source))
                source = zipfile.ZipFile(data_stream, "r")
        elif isinstance(source, bytes):  # from bytes
            data_stream = io.BytesIO(source)
            self.source_data = source
            source = zipfile.ZipFile(data_stream, "r")
        self.access_lock = RLock()
        "Multithreading access lock"
        self.zip_archive: zipfile.ZipFile = source
        "The zip archive which provides the file data"
        self.file_count = len(self.zip_archive.filelist)
        if params.get("fetch_file_list", False):
            self.handle_fetch_file_list()

    def _get_source_identifier(self) -> str:
        if len(self.source_identifier) == 0 and self.source_data is not None:
            # if we have no reliable path we need to checksum the file, very
            # expensive, but what shall we do :-/
            self.source_identifier = hashlib.md5(self.source_data).hexdigest()
        return f"{self.source_identifier}|"

    def _read_file_int(self, filename: str) -> bytes | None:
        with self.access_lock:
            try:
                return self.zip_archive.read(filename)
            except KeyError:
                raise FileNotFoundError(f"Could not find {filename}")

    def exists(self, filename: str) -> bool:
        with self.access_lock:
            if self._file_list:
                return super().exists(filename)
            return filename in self.zip_archive.namelist()

    def handle_get_next_filename(self, iterator: FileSourceIterator) -> \
            tuple[str, int] | None:
        with self.access_lock:
            if self._file_list is None:
                while True:
                    if iterator.file_index >= self.file_count:
                        return None
                    index = iterator.file_index
                    iterator.file_index += 1
                    if not self.handle_file_list_filter(
                            self.zip_archive.filelist[index].filename):
                        continue
                    return self.zip_archive.filelist[index].filename, \
                           self.zip_archive.filelist[index].file_size
            else:
                return super().handle_get_next_filename(iterator)

    def handle_fetch_file_list(self, force: bool = False):
        with self.access_lock:
            if self._file_list is not None and not force:
                return
            cleaned_list = [element for element in self.zip_archive.filelist if
                            self.handle_file_list_filter(element.filename)]
            elements = sorted(cleaned_list,
                              key=lambda element: element.filename)
            self.update_file_list(
                [FileListEntry(filename=element.filename,
                               file_size=element.file_size) for element in
                 elements])

    def close(self):
        with self.access_lock:
            self.zip_archive.close()
            super().close()
