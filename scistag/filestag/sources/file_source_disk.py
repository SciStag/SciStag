"""
Implements the :class:`FileSourceDisk` class which allows iterating files from a
 local directory
"""
from __future__ import annotations
import glob
import os
from datetime import datetime

from scistag.filestag import FilePath
from scistag.filestag.file_source import FileSource, FileListEntry, \
    FileSourcePathOptions


class FileSourceDisk(FileSource):
    """
    FileSource implementation for processing files on the disk, stored in one or multiple directories.

    All you have to do is to provide a folder name and you can easily iterate through all files in that directory:

    ``for cur_file in FileSourceDisk("./image_folder", mask="*.png"): ...``
    """

    def __init__(self, path: str, **params):
        """
        :param path: The source path to search in
        :param params: Additional parameters. See :class:`~scistag.filestag.file_source.FileSource` for the full
        parameter list.
        """
        super().__init__(**params)
        assert len(path) > 0
        self.search_path = os.path.normpath(path)
        self._create_file_list_int()

    def _get_source_identifier(self) -> str:
        return f"{self.search_path}|"

    def _read_file_int(self, filename: str) -> bytes | None:
        full_filename = os.path.normpath(self.search_path + "/" + filename)
        if os.path.exists(full_filename):
            with open(full_filename, "rb") as cur_file:
                return cur_file.read()
        else:
            raise FileNotFoundError(f"Could not find {full_filename}")

    def handle_fetch_file_list(self, force: bool = False):
        if self._file_list is not None and not force:
            return
        cleaned_path = os.path.normpath(self.search_path)
        name_list = glob.glob(self.search_path + "/**",
                              recursive=self.recursive)
        cpl = len(cleaned_path)
        name_list = [element[cpl + 1:] for index, element in
                     enumerate(name_list) if os.path.isfile(element)]
        full_list = [FileListEntry(filename=cur_element,
                                   file_size=os.path.getsize(
                                       self.search_path + "/" +
                                       cur_element),
                                   createed=datetime.fromtimestamp(
                                       os.path.getctime(
                                           self.search_path + "/" +
                                           cur_element)),
                                   modified=datetime.fromtimestamp(
                                       os.path.getmtime(
                                           self.search_path + "/" +
                                           cur_element))
                                   )
                     for cur_element in name_list]
        full_list = [element for element in full_list if
                     self.handle_file_list_filter(element)]
        elements = sorted(full_list, key=lambda x: x.filename)
        self.update_file_list(elements)

    def get_absolute(self, filename: str,
                     options: FileSourcePathOptions | None = None) -> \
            str | None:
        return FilePath.absolute(self.search_path + "/" + filename)

    def close(self):
        super().close()
