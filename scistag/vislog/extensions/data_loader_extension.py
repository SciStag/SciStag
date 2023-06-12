"""
Implements the data source extension which tracks external dependencies
"""
from __future__ import annotations
import os
import typing
from typing import Dict, Union

from scistag.common import DataObserver
from scistag.filestag import FileStag, FileDataObserver
from scistag.vislog import BuilderExtension, LogBuilder

if typing.TYPE_CHECKING:
    from scistag.vislog.widgets.cells import Cell


class DataLoaderExtension(BuilderExtension):
    """
    Tracks and provides access to external dependencies such as files or shared data
    frames.
    """

    def __init__(self, builder: LogBuilder):
        """
        :param builder: The builder object
        """
        super().__init__(builder=builder)
        self._sources: Dict[str, DataObserver] = {}
        """List of observed elements"""

    def normalized_source(self, source: str) -> str:
        """
        Normalizes the source link, e.g. a relative to an absolute path

        :param source: The data source
        :return: The corrected path
        """
        if isinstance(source, str):
            return os.path.abspath(source)
        return source

    def add_dependency(self, source: str) -> bool:
        """
        Adds a data dependency to the current cell for automatic cache clearance and
        triggering the auto-reloader (if enabled) when an included file gets
        modified.

        :param source: The data source or the name of the file which shall be tracked.
            By default only local files are observed.
        """
        if not FileStag.is_simple(source):
            return False
        cur_cell = self.page_session.get_active_cell()
        source = self.normalized_source(source)
        if cur_cell is not None:
            cur_cell.add_data_dependency(source)
        return False

    def add_source(self, source: str, cell: Union["Cell", None] = None) -> None:
        """
        Adds a source to be observed

        :param source: The source location
        :param cell: The cell which is using the new data source
        """
        if source in self._sources:
            return
        if isinstance(source, str):
            if FileStag.exists(source):
                fdo = FileDataObserver(source)
                self._sources[source] = fdo

    def get_hash(self, source: str) -> int | None:
        """
        Returns the hash of a current dependency

        :param source: The source identifier such as a filename
        :return: The source's hash if the source is known, otherwise None
        """
        source = self.normalized_source(source)
        if source in self._sources:
            return self._sources[source].hash_int()
        return None

    def handle_cell_modified(self, cell: "Cell") -> None:
        """
        Is called from a cell when it got modified

        :param cell: The cell which was modified
        """
        pass

    def add_data_dependency(self, filename: str):
        raise RuntimeError(
            "This method is not available in this class. "
            "Please call add_dependency instead"
        )
