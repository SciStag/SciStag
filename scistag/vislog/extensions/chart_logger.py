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
from scistag.filestag import FileStag, FilePath
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
        lines = code.split("\n")
        lines = [line.lstrip(" ").lstrip("\t") for line in lines]
        lines = [line for line in lines if len(lines) > 0]
        code = "\n".join(lines)
        self.builder.md("```mermaid\n" + code + "\n```")

    def embed(self, filename: str, watch=True, extension: str | None = None) -> bool:
        """
        Embeds a chart file. The file type will be auto-detected if no extension is
            passed.

        :param filename: The data to embed
        :param watch: Defines if the file shall be watched and the diagrams be
            auto-updated if necessary.
        :param extension: The file type, e.g. "mmd" in case no name is passed
        """
        if not isinstance(filename, str):
            raise TypeError("Only filenames allowed as source at the moment")
        if extension is None:
            extension = FilePath.split_ext(filename)[-1]
        if extension not in {".mmd", ".mermaid"}:
            raise ValueError("Unsupported file extension")
        if watch:
            self.add_data_dependency(filename)
        data = FileStag.load_text(filename)
        if data is not None:
            data = data.replace("\r\n", "\n")
        if data is not None:
            self.mmd(data)
            return True
        return False
