"""
Defines the class :class:`BuilderExtension` which is the base class
for LogBuilder extensions such as adding markdown or HTML.
"""
from scistag.filestag import FileStag
from scistag.vislog import LogBuilder


class BuilderExtension:
    """
    Helper class which adds a specific logging feature to LogBuilder
    such as logging tables or logging markdown.
    """

    def __init__(self, builder: LogBuilder):
        """
        :param builder: The builder object with which we write to the log
        """
        self.builder: LogBuilder = builder
        """
        The builder we are adding our content to
        """
        self.page_session = builder.page_session
        """
        Defines the target page which holds the page content for each data type
        """
        self.options = builder.options
        """
        Reference the builder's options
        """

    def add_data_dependency(self, source: str) -> bool:
        """
        Adds a data dependency to the current cell for automatic cache clearance and
        triggering the auto-reloader (if enabled) when an included file gets
        modified.

        :param source: The data source or the name of the file which shall be tracked.
            By default only local files are observed.
        """
        return self.builder.data_loader.add_dependency(source)
