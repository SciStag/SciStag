"""
Implements the :class:`ChartLogger` extension for LogBuilder to log
collections and diagrams.
"""
from __future__ import annotations

from scistag.common.trees.text_tree import (
    TextTreeNode,
    TextTreeBuilderOptions,
    TextTree,
)
from scistag.filestag import FileStag
from scistag.vislog import BuilderExtension, LogBuilder


class ChartLogger(BuilderExtension):
    """
    The chart logger allows the easy integration of charts such as mermaid charts
    into the log.
    """

    def __init__(self, builder: LogBuilder):
        """
        :param builder: The builder we are using to write to the log
        """
        super().__init__(builder)

    def mmd(self, code: str) -> None:
        """
        Embeds mermaid chart and diagram code into the documentation.

        See https://mermaid.js.org/

        :param code: The mermaid code
        """
        self.builder.md("```mermaid\n" + code + "\n```")

    def embed(self, filename: str, watch=True, extension: str | None = None):
        """
        Embeds a chart file. The file type will be auto-detected if no extension is
            passed.

        :param filename: The source filename
        :param watch: Defines if the file shall be watched and the diagrams be
            auto-updated if necessary.
        :param extension: The file type, e.g. "mmd" in case no name is passed
        """
        if watch:
            self.add_data_dependency(filename)
        data = FileStag.load_text(filename)
        if data is not None:
            self.mmd(data)
