"""
Implements the class :class:`VisualMarkdownBuilderExtension` which adds Markdown
support to the VisualLogBuilder.
"""

from __future__ import annotations

from scistag.filestag import FileStag, FileSourceTypes
from scistag.vislog import VisualLogBuilder, VisualLogBuilderExtension
from scistag.vislog.visual_log import MD, HTML, TXT


class VisualMarkdownBuilderExtension(VisualLogBuilderExtension):
    """
    Adds the possibility to log single markdown lines or even whole Markdown
    files to a VisualLog.
    """

    def __init__(self, builder: VisualLogBuilder):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)
        self.add = self.__call__

    def __call__(self, text: str, exclude_targets: set[str] | None = None) \
            -> VisualLogBuilder:
        """
        Adds a markdown section.

        Requires the Markdown package to be installed.

        :param text: The text to parse
        :param exclude_targets: Defines the target to exclude
        :return: The builder
        """
        lines = text.split("\n")
        # use equal trim when triple quotation marks were used
        if len(lines) > 1 and len(lines[0]) <= 1:
            trimmed = lines[1].lstrip(" \t")
            trim_dist = len(lines[1]) - len(trimmed)
            for index, line in enumerate(lines):
                if len(line) > trim_dist:
                    lines[index] = line[trim_dist:]
            text = "\n".join(lines)
        if exclude_targets is None:
            exclude_targets = set()
        import markdown
        from markdown.extensions.tables import TableExtension
        parsed = markdown.markdown(text, extensions=['tables'])
        if MD not in exclude_targets:
            self.builder.add_md(text + "\n")
        if HTML not in exclude_targets:
            self.builder.add_html(parsed + "\n")
        if TXT not in exclude_targets:
            self.builder.add_txt(text)
        self.builder.clip_logs()
        return self.builder

    def embed(self, source: FileSourceTypes,
              encoding="utf-8") -> VisualLogBuilder:
        """
        Embeds a markdown file into the log

        :param source: The filename or a compatible file source
        :param encoding: The file's encoding
        :return: The builder
        """
        if isinstance(source, str):
            self.add_dependency(source)
        data = FileStag.load_text(source, encoding=encoding)
        if data is not None:
            self.add(data)
        return self.builder
