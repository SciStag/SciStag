"""
Defines BasicLogger which provides functions for classic logging
with info, warning, error etc.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

from scistag.logstag import LogLevel
from scistag.vislog.extensions.builder_extension import BuilderExtension

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import VisualLogBuilder


class BasicLogger(BuilderExtension):
    """
    Helper class for classic logging via info, debug, warning etc.
    """

    def __init__(self, builder: "VisualLogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)
        self.add = self.__call__
        self.level_tag = {
            LogLevel.INFO: "[INFO]",
            LogLevel.DEBUG: "[DEBUG]",
            LogLevel.WARNING: "[WARNING]",
            LogLevel.ERROR: "[ERROR]",
            LogLevel.CRITICAL: "[CRITICAL]",
        }
        "Tags to be added in front of the single log levels"
        self.level_color = {
            LogLevel.DEBUG: "blue",
            LogLevel.WARNING: "#999900",
            LogLevel.ERROR: "red",
            LogLevel.CRITICAL: "purple",
        }
        "Colors for the single log levels"

    def _log_advanced(self, text, level: LogLevel) -> VisualLogBuilder:
        """
        Detects tables and other objects in a log and pretty prints the tables
        while keeping the other log data intact

        :param text: The log text
        :param level: The log level
        :return: The log builder
        """
        lines = text.split("\n")
        common_block = ""
        cur_table = None

        def flush_table():
            """
            Flushes the current table if one has been prepared
            """
            nonlocal cur_table
            if cur_table is not None:
                self.builder.table(cur_table)
                self.builder.br()
                cur_table = None

        for line in lines:
            from scistag.vislog.visual_log import TABLE_PIPE

            if line.startswith(TABLE_PIPE):
                if len(common_block) > 0:
                    self.add(common_block, level=level)
                    common_block = ""
                if cur_table is None:
                    cur_table = []
                elements = [
                    element.lstrip(" ").rstrip(" ") for element in line.split("|")
                ]
                if len(elements) > 2:
                    elements = elements[1:-1]
                cur_table.append(elements)
            else:
                # when back to normal mode visualize current in-progress element
                flush_table()
                common_block += line + "\n"
        flush_table()
        if len(common_block) > 0:
            self.add(common_block, level=level)
        return self.builder

    def __call__(
        self,
        *args: Any,
        level: LogLevel | str | None = None,
        detect_objects: bool = False,
        no_break: bool = False,
        space: str = " ",
    ) -> VisualLogBuilder:
        """
        Adds a log text to the log

        :param args: The text arguments to add to the log
        :param level: The importance / category of the log entry. If None is
            provided the text will be added w/o modifications and tag.
        :param detect_objects: Defines if special objects such as tables shall
            be detected and printed beautiful
        :param no_break: If set linebreaks will be avoided, e.g. a cell inside
            a table.
        :param space: The character or text to be used for spaces
        :return: The builder
        """
        if level is not None and isinstance(level, str):
            level = LogLevel(level)
        if len(args) == 0 or args[0] is None:
            text = "None"
        else:
            elements = [str(element) for element in args]
            text = space.join(elements)
        from scistag.vislog.visual_log import TABLE_PIPE

        if detect_objects and TABLE_PIPE in text:
            self._log_advanced(text, level)
            return self.builder
        md_text = text
        if level is not None and level in self.level_tag:
            md_text = f"<b>{self.level_tag[level]}</b>: {text}"
            text = self.level_tag[level] + ": " + text
        escaped_text = self.builder.encode_html(text)
        if level in self.level_color:
            self.builder.add_html(
                f'<p class="logtext" style="color:{self.level_color[level]}">'
                f"{self.builder.html_linebreaks(escaped_text)}</p>"
                f"<br>\n\n"
            )
        else:
            self.builder.add_html(
                f'<p class="logtext">'
                f"{self.builder.html_linebreaks(escaped_text)}</p>"
                f"<br>\n\n"
            )

        md_lines = md_text.split("\n")
        if self.target_log.markdown_html and level is not None:
            md_lines = "<br>".join(md_lines) + "<br>"
            if level in self.level_color:
                self.builder.add_md(
                    f'<span style="color:{self.level_color[level]}">{md_lines}'
                    f"</span>\n"
                )
            else:
                self.builder.add_md(f"<span>" f"</span>")

        else:
            md_lines = "\n\n".join(md_lines)
            if no_break:
                self.builder.add_md(f"{md_lines}")
            else:
                self.builder.add_md(f"{md_lines}\n")
        self.builder.add_txt(text)
        self.builder.handle_modified()
        return self.builder

    def info(self, *args, **kwargs) -> VisualLogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.add(*args, **kwargs, level=LogLevel.INFO)
        return self.builder

    def debug(self, *args, **kwargs) -> VisualLogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.add(*args, **kwargs, level=LogLevel.DEBUG)
        return self.builder

    def warning(self, *args, **kwargs) -> VisualLogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.add(*args, **kwargs, level=LogLevel.WARNING)
        return self.builder

    def error(self, *args, **kwargs) -> VisualLogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.add(*args, **kwargs, level=LogLevel.ERROR)
        return self.builder

    def critical(self, *args, **kwargs) -> VisualLogBuilder:
        """
        Logs a critical error

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.add(*args, **kwargs, level=LogLevel.CRITICAL)
        return self.builder
