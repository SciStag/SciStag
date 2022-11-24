"""
The class :class:`FileSourceObserver` observers a specified FileSource such
as a directory or cloud storage and trigger its callbacks or changes its
hash value when ever a file was modified.
"""

from scistag.common.observer import Observer
from scistag.filestag.file_source import FileSource


class FileSourceObserver(Observer):
    """
    The FileSourceObserver creates a hash of a defined FileSource by combining
    the hashes of all filenames, sizes and time stamps into a single hash.

    When ever a single file is changed the observer is triggered and it's
    hash value changed.
    """

    def __init__(self, source: FileSource,
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
        self.source = source
        "The file source"

    def hash_int(self) -> str:
        self.source.refresh()
        return self.source.get_hash(max_content_size=self.max_content_size)
