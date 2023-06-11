"""
The class :class:`FileDataObserver` observers a specified FileSource such
as a directory or cloud storage and trigger its callbacks or changes its
hash value when ever a file was modified.
"""

from __future__ import annotations

import hashlib
import io
import os

from scistag.common.observer import DataObserver
from scistag.filestag import FileStag
from scistag.filestag.file_source import FileSource


class FileDataObserver(DataObserver):
    """
    The FileDataObserver creates a hash of a defined file or FileSource by combining
    the hashes of all filenames, sizes and time stamps into a single hash.

    When ever a single file is changed the observer is triggered and it's
    hash value changed.
    """

    def __init__(
        self,
        source: FileSource | list[FileSource | str] | None | str,
        max_content_size: int = 0,
        refresh_time_s: float = 1.0,
    ):
        """
        :param source: The file source we shall observe
        :param max_content_size: Defines the maximum size in bytes up to which
            not just file stamps and file size are evaluated but actually also
            the content of the files themselves.
        :param refresh_time_s: The minimum time gap between a refresh
        """
        super().__init__(refresh_time_s=refresh_time_s)
        self.max_content_size = max_content_size
        """
        The maximum size in bytes up to which the actual content of a file
        may be evaluated.
        """
        if source is None:
            source = []
        elif isinstance(source, FileSource):
            source = [source]
        elif isinstance(source, str):
            source = [source]
        else:
            raise TypeError("Unsupported data type")
        self.sources: list[FileSource] = [
            element for element in source if isinstance(element, FileSource)
        ]
        "The file sources to observe"
        self.files = [element for element in source if isinstance(element, str)]
        "The list of single files to observe"

    def add(self, source: FileSource | str):
        """
        Adds a new file source or single file to the list of observed targets

        :param source: The source, either a filename or a FileSource object
        """
        if isinstance(source, str):
            if not FileStag.is_simple(source):
                raise ValueError("Only local files supported as of now")
            self.files.append(source)
        else:
            self.sources.append(source)

    def hash_int(self) -> int:
        hashes = "hi"
        for cur_source in self.sources:
            cur_source.refresh()
            hashes += cur_source.get_hash(max_content_size=self.max_content_size)
        for element in self.files:
            if not FileStag.is_simple(element):
                raise ValueError("Only local files supported as of now")
            mod_date = os.path.getmtime(element)
            size = os.path.getsize(element)
            content_hash: str = ""
            if size < self.max_content_size:
                content_hash = hashlib.md5(FileStag.load(element)).hexdigest()
            stream = io.BytesIO()
            stream.write(content_hash.encode("utf-8"))
            stream.write(int(mod_date * 10).to_bytes(8, "little", signed=True))
            stream.write(size.to_bytes(8, "little", signed=True))
            hashes += hashlib.md5(stream.getvalue()).hexdigest()
        return int(hashlib.md5(hashes.encode("utf-8")).hexdigest(), 16)
