"""
Implements the data source extension which tracks external dependencies
"""
import os

from scistag.vislog import BuilderExtension, LogBuilder


class DataSourceExtension(BuilderExtension):
    """
    Tracks and provides access to external dependencies such as files or shared data
    frames.
    """

    def __init__(self, builder: LogBuilder):
        """
        :param builder: The builder object
        """
        super().__init__(builder=builder)

    def add_dependency(self, source: str):
        """
        Adds a data dependency to the current cell for automatic cache clearance and
        triggering the auto-reloader (if enabled) when an included file gets
        modified.

        :param source: The data source or the name of the file which shall be tracked.
            By default only local files are observed.
        """
        cur_cell = self.page_session.get_active_cell()
        if isinstance(source, str):
            source = os.path.abspath(source)
        if cur_cell is not None:
            cur_cell.add_data_dependency(source)

    def add_data_dependency(self, filename: str):
        raise RuntimeError(
            "This method is not available in this class. "
            "Please call add_dependency instead"
        )
