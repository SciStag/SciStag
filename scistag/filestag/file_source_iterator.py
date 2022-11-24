from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.filestag import FileSource
    from scistag.filestag.file_source import FileSourceElement, FileListEntry


class FileSourceIterator:
    """
    Iterator providing the data from a file source
    """

    def __init__(self, source: "FileSource"):
        """
        :param source: The file source to provide the data for
        """
        self.source = source
        "The FileSource which created this iterator"
        self.processing_data = {}
        """
        Additional, user defined parameters you can store here to make them
        accessible to your callback for example
        """
        self.file_index = 0
        "The index of all found files (including skipped ones)"
        self.processed_file_count = 0
        "The index of all really processed files"
        self.current_file_size = 0
        """
        The size of the file which is currently being handled. Not available
        for all file sources. (0 in that case)
        """

    def __next__(self) -> Union["FileSourceElement", None]:
        """
        Requests the next data from the file source

        :return: The data object
        """
        result = self.source.handle_next(self)
        if result is None:
            raise StopIteration
        return result


@dataclass
class FileIterationData:
    """
    Provides the data to filter single file entries
    """
    file_source: "FileSource"
    "The :class:`FileSource` object for which the decision is made"
    file_index: int
    "The file's index"
    element: "FileListEntry"


FilterCallback = Callable[[FileIterationData], Union[bool, str]]
"""
Shall verify if a function shall be handled or ignored.

Parameters:
* The file iteration data describing the current file to handle. 
    See :class:`FileIterationData`.

Return:
* True if the file shall be processed, False if not. Alternatively a string 
    if the file shall be processed but renamed.
"""
