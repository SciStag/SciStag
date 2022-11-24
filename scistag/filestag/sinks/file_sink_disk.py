"""
Defines the class :class:`FileSinkDisk` which stores all added files directly
to a folder on disk.
"""
from __future__ import annotations

from scistag.filestag import FileSink, FileStorageOptions, FilePath, FileStag


class FileSinkDisk(FileSink):
    """
    Defines a file basic file sink which stores all files in a defined target
    folder o disk.
    """

    def __init__(self, target: str, create_dirs=True, **params):
        """
        :param target: The sink's storage target folder
        :param create_dirs: Defines if directories may automatically be created,
            True by default.
        """
        super().__init__(target=target, **params)
        self.create_dirs = create_dirs
        "Defines if missing directories may automatically be created"

    def _store_int(self, filename: str, data: bytes, overwrite: bool,
                   options: FileStorageOptions | None = None) -> bool:
        filename = self._target + "/" + filename
        tar_dir = FilePath.dirname(filename)
        if not FilePath.exists(tar_dir):
            if not self.create_dirs:
                return False
            FilePath.make_dirs(tar_dir, exist_ok=True)
        if not overwrite and FilePath.exists(filename):
            return False
        return FileStag.save(filename, data)
