"""
Defines the class :class:`LogBackup` which contains the copy of a log's data, for
example to insert it into another log.
"""

from __future__ import annotations

import os

from pydantic import BaseModel

from scistag.filestag import FileStag


class LogBackup(BaseModel):
    """
    Contains the backup of a log and all necessary data to integrate it into
    another log.
    """

    data: dict[str, bytes] = {}
    "The logs representation of each format"

    def save_to_disk(self, path: str, index_name: str = "index"):
        """
        Saves the backups content into given target directory

        :param path: The target path
        :param index_name: The name of the index file
        """
        os.makedirs(f"{path}", exist_ok=True)
        for cur_format in self.data:
            FileStag.save(f"{path}/{index_name}.{cur_format}", self.data[cur_format])
