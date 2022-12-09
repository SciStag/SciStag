"""
Defines the class :class:`VisualLogBuilderExtension` which is the base class
for VisualLogBuilder extensions such as adding markdown or HTML.
"""

from scistag.vislog import VisualLogBuilder


class VisualLogBuilderExtension:
    """
    Helper class which adds a specific logging feature to VisualLogBuilder
    such as logging tables or logging markdown.
    """

    def __init__(self, builder: VisualLogBuilder):
        """
        :param builder: The builder object with which we write to the log
        """
        self.builder: VisualLogBuilder = builder
        """
        The builder we are adding our content to
        """
        self.log = self.builder.target_log
        """
        The log object
        """

    def add_dependency(self, filename: str):
        """
        Adds a file dependency to the log for automatic cache clearance and
        triggering the auto-reloader (if enabled) when an included file gets
        modified.

        :param filename: The name of the file which shall be tracked. By
            default only local files are observed.
        """
        self.builder.add_file_dependency(filename)