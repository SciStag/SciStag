"""
Defines BasicLogger which provides functions for classic logging
with info, warning, error etc.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

from scistag.logstag import LogLevel
from scistag.vislog import MD
from scistag.vislog.extensions.builder_extension import BuilderExtension

if TYPE_CHECKING:
    from scistag.vislog.log_builder import LogBuilder


class BasicLogger(BuilderExtension):
    """
    Helper class for classic logging via info, debug, warning etc.
    """

    def __init__(self, builder: "LogBuilder"):
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
            LogLevel.DEBUG: "#3355FF",
            LogLevel.WARNING: "#999900",
            LogLevel.ERROR: "#EE1111",
            LogLevel.CRITICAL: "purple",
        }
        "Colors for the single log levels"

    def _log_advanced(self, text, level: LogLevel) -> LogBuilder:
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
        br: bool = True,
        space: str = " ",
    ) -> LogBuilder:
        """
        Adds a log text to the log

        :param args: The text arguments to add to the log
        :param level: The importance / category of the log entry. If None is
            provided the text will be added w/o modifications and tag.
        :param detect_objects: Defines if special objects such as tables shall
            be detected and printed beautiful
        :param br: Defines if a linebreak shall be added, e.g. a cell inside
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
            split_t = text.split("\n")
            md_text = "\n".join(
                [f"<b>{self.level_tag[level]:9s}</b> {cur}" for cur in split_t]
            )
            text = "\n".join([f"{self.level_tag[level]:9s} {cur}" for cur in split_t])
        escaped_text = self.builder._encode_text_html(text)
        br_code = "<br>" if br else ""
        if level in self.level_color:
            self.builder.add_html(
                f'<span class="logtext" style="color:{self.level_color[level]:9s}">'
                f"{self.builder._html_linebreaks(escaped_text)}</span>"
                f"{br_code}"
            )
        else:
            self.builder.add_html(
                f'<span class="logtext">'
                f"{self.builder._html_linebreaks(escaped_text)}</span>"
                f"{br_code}"
            )

        md_lines = md_text.split("\n")
        if level is not None:
            md_lines = "\n".join(md_lines)
            if level in self.level_color:
                self.builder.add_md(
                    f'<span style="white-space: pre-wrap;color:'
                    f'{self.level_color[level]}">{md_lines}{br_code}'
                    f"</span>",
                    br=False,
                )
            else:
                self.builder.add_md(
                    f"<span style='white-space: pre-wrap;'>{md_lines}{br_code}"
                    f"</span>",
                    br=False,
                )

        else:
            lines = "\n".join(md_lines)
            md_lines = f"<span style='white-space: pre-wrap;'>{lines}{br_code}</span>"
            self.builder.add_md(f"{md_lines}", br=br)
        self.builder.add_txt(text, br=br)
        return self.builder

    def info(self, *args, **kwargs) -> LogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.add(*args, **kwargs, level=LogLevel.INFO)
        return self.builder

    def debug(self, *args, **kwargs) -> LogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.add(*args, **kwargs, level=LogLevel.DEBUG)
        return self.builder

    def warning(self, *args, **kwargs) -> LogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.add(*args, **kwargs, level=LogLevel.WARNING)
        return self.builder

    def error(self, *args, **kwargs) -> LogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.add(*args, **kwargs, level=LogLevel.ERROR)
        return self.builder

    def critical(self, *args, **kwargs) -> LogBuilder:
        """
        Logs a critical error

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.add(*args, **kwargs, level=LogLevel.CRITICAL)
        return self.builder
