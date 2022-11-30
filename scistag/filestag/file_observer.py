"""
The class :class:`FileObserver` observers a specified FileSource such
as a directory or cloud storage and trigger its callbacks or changes its
hash value when ever a file was modified.
"""

from __future__ import annotations

import hashlib

from scistag.common.observer import Observer
from scistag.filestag.file_source import FileSource


class FileObserver(Observer):
    """
    The FileObserver creates a hash of a defined FileSource by combining
    the hashes of all filenames, sizes and time stamps into a single hash.

    When ever a single file is changed the observer is triggered and it's
    hash value changed.
    """

    def __init__(self, source: FileSource | list[FileSource] | None,
                 max_content_size: int = 0,
                 refresh_time_s: float = 1.0):
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
        elif not isinstance(source, list):
            source = [source]
        self.sources: list[FileSource] = source
        "The file sources to observe"
        self.files = []
        "The list of single files to observe"

    def add(self, source: FileSource | str):
        if isinstance(source, str):
            self.files.append(source)
        else:
            self.sources.append(source)

    def hash_int(self) -> str:
        hashes = "hi"
        for cur_source in self.sources:
            cur_source.refresh()
            hashes += cur_source.get_hash(
                max_content_size=self.max_content_size)
        # TODO Add single file hashes
        return hashlib.md5(hashes.encode("utf-8")).hexdigest()
