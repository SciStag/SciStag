"""
Implements the class :class:`MarkdownLogger` which adds Markdown
support to the LogBuilder.
"""

from __future__ import annotations

from scistag.filestag import FileStag, FileSourceTypes
from scistag.vislog import LogBuilder, BuilderExtension
from scistag.vislog.visual_log import MD, HTML, TXT


class MarkdownLogger(BuilderExtension):
    """
    Adds the possibility to log single markdown lines or even whole Markdown
    files to a VisualLog.
    """

    def __init__(self, builder: LogBuilder):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)
        self.add = self.__call__
        self.log_html_only: bool = False
        """If defined no markdown will be written temporarily but the HTML output
        will be used instead"""

    def __call__(
        self,
        text: str,
        exclude_targets: set[str] | None = None,
        br=True,
    ) -> LogBuilder:
        """
        Adds a markdown section.

        Requires the Markdown package to be installed.

        :param text: The text to parse
        :param exclude_targets: Defines the target to exclude
        :param br: Defines if a linebreak shall be inserted
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

        parsed = self.quick_parse(text)
        if parsed is None:
            parsed = markdown.markdown(text, extensions=["tables"])
        if MD not in exclude_targets:
            self.builder.add_md(text, br=br)
        if HTML not in exclude_targets:
            if parsed.startswith("<p>") and parsed.endswith("</p>"):
                parsed = parsed[3:-4]
            self.builder.add_html(parsed + "\n")
        if TXT not in exclude_targets:
            self.builder.add_txt(text, br=br)
        self.builder.handle_modified()
        return self.builder

    @staticmethod
    def quick_parse(text: str):
        """
        Tries to parse simple markdown

        :param text: The text to be parsed
        :return: The result if simple parsing was possible
        """
        parsed = None
        spaceless = text.strip(" ")
        if len(text) < 80 and "\n" not in text:
            if spaceless.isalnum():  # just text
                parsed = text
            elif (  # bold
                len(text)
                and text.startswith("**")
                and text.endswith("**")
                and text[2:-2].strip(" ").isalnum()
            ):
                parsed = f"<strong>{text[2:-2]}</strong>"
        elif (  # italic
            len(text)
            and text.startswith("*")
            and text.endswith("*")
            and text[1:-1].strip(" ").isalnum()
        ):
            parsed = f"<strong>{text[2:-2]}</strong>"
        return parsed

    def embed(self, source: FileSourceTypes, encoding="utf-8") -> LogBuilder:
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
        else:
            raise ValueError("Invalid file data")
        return self.builder
