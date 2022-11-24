"""
Implements the class :class:`FileSinkZip` which allows collecting file
elements in an in-memory zip archive.
"""

from __future__ import annotations

import zipfile

from scistag.filestag.file_sink import FileStorageOptions
from scistag.filestag.sinks.archive_file_sink import ArchiveFileSinkProto


class FileSinkZip(ArchiveFileSinkProto):
    """
    Defines a file sink which stores all files in a zip archive -
    by default an archive in the memory.

    After all files have been added they can be received via :meth:`get_data`
    as a single bytes string.
    """

    def __init__(self, target: str, compression=20, **params):
        """
        :param target: The sink's storage target
        :param compression: The compression level to be used from 0 (pure
            storage) to 100 (best compression)
        :param params: Additional initializer parameters. See :class:`FileSink`.
        """
        from scistag.filestag import MemoryZip
        super().__init__(target=target, **params)
        comp_level = min(max((compression // 10), 0), 9)
        comp_method = (zipfile.ZIP_STORED if comp_level == 0 else
                       zipfile.ZIP_DEFLATED)
        self.archive = MemoryZip(compresslevel=comp_level,
                                 compression=comp_method)

    def _store_int(self, filename: str, data: bytes, overwrite: bool,
                   options: FileStorageOptions | None = None) -> bool:
        if not overwrite and filename in self.archive.namelist():
            return False
        self.archive.writestr(filename, data)
        return True

    def get_value(self) -> bytes:
        if not self._closed:
            self.close()
        return self.archive.to_bytes()

    def close(self):
        super().close()
        self.archive.close()
