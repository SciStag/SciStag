"""
Defines the class :class:`VisualLogBuilder` which is the main interface for
adding data in a VisualLog.
"""

from __future__ import annotations

import time
from collections import Counter
from typing import Optional, Any, TYPE_CHECKING
import io

import base64
import html

import hashlib

import numpy as np
import pandas as pd
from filetype import filetype
from matplotlib import pyplot as plt

from scistag.filestag import FileStag, FilePath
from scistag.imagestag import Image, Canvas, PixelFormat, Size2D
from scistag.logstag import LogLevel

from scistag.logstag.visual_log.visual_log import VisualLog, MD, TXT, HTML, \
    TABLE_PIPE
from scistag.plotstag import Figure, Plot, MPHelper

if TYPE_CHECKING:
    from scistag.logstag.visual_log.pyplot_log_context import PyPlotLogContext


class VisualLogBuilder:
    """
    Defines an interface to all major log writing functions
    for the creation of a VisualLog document.

    Can be overwritten to be provided as callback target for dynamic
    documentation creation.
    """

    def __init__(self, log: "VisualLog"):
        """
        :param log: The log to which the content shall be added.
        """
        self.log: "VisualLog" = log
        "The main logging target"
        self.logs = self.log._logs
        self.forward_targets: dict[str, VisualLogBuilder] = {}
        "List of logs to which all rendering commands shall be forwarded"
        self.name_counter = Counter()
        "Counter for file names to prevent writing to the same file twice"
        self.title_counter = Counter()
        "Counter for titles to numerate the if appearing twice"
        self._total_update_counter = 0
        "The total number of updates to this log"
        self._update_counter = 0
        # The amount of updates since the last statistics update
        self._last_statistic_update = time.time()
        "THe last time the _update rate was computed as time stamp"
        self._update_rate: float = 0
        # The last computed updated rate in updates per second
        from .visual_log_test_helper import VisualLogTestHelper
        self.test = VisualLogTestHelper(self)
        from .visual_image_logger import VisualImageLogger
        self.image = VisualImageLogger(self)

    @property
    def max_fig_size(self) -> Size2D:
        """
        The maximum figure size in pixels
        """
        return self.log.max_fig_size

    def clear(self):
        """
        Clears the whole log (excluding headers and footers)
        """
        self.name_counter = Counter()
        self.title_counter = Counter()
        for key in self.logs.keys():
            self.logs[key].clear()

    def embed(self, log: VisualLog):
        """
        Embeds another VisualLog's content into this one

        :param log: The source log
        """
        for cur_format in self.log.log_formats:
            if cur_format in log.log_formats:
                self.logs[cur_format].append(log.get_body(cur_format))

    def table(self, data: list[list[any]], index=False, header=False):
        """
        Adds a table to the log.

        :param data: The table data. A list of rows including a list of
            columns.

            Each row has to provide the same count of columns.

            At the moment only string content is supported.
        :param index: Defines if the table has an index column
        :param header: Defines if the table has a header
        """
        code = '<table class="log_table">\n'
        for row_index, row in enumerate(data):
            tabs = "\t"
            code += f"{tabs}<tr>\n"
            for col_index, col in enumerate(row):
                code += f"\t{tabs}<td>\n{tabs}\t"
                assert isinstance(col, str)  # more types to be supported soon
                if index and col == 0:
                    code += "<b>"
                major_cell = (row_index == 0 and header or
                              col_index == 0 and index)
                if major_cell:
                    code += f"<b>{col}</b>"
                else:
                    code += col
                if index and col == 0:
                    code += "</b>"
                code += f"\n{tabs}</td>\n"
                tabs = tabs[0:-1]
            code += f"{tabs}</tr>\n"
        code += "</table>\n"
        self._add_html(code)
        for row in data:
            row_text = "| "
            for index, col in enumerate(row):
                row_text += col + " | "
            self._add_txt(row_text, md=True)
        return self

    def evaluate(self, code: str, log_code: bool = True) -> Any:
        """
        Runs a piece of code and returns it's output

        :param code: The code to execute
        :param log_code: Defines if the code shall be added to the log
        :return: The returned data (if any)
        """
        import inspect
        frame = inspect.currentframe()
        result = eval(code, frame.f_back.f_globals, frame.f_back.f_locals)
        if log_code:
            if result is not None:
                self.code(code + f"\n>>> {result}")
            else:
                self.code(code)
        return result

    def title(self, text: str):
        """
        Adds a title to the log

        :param text: The title's text
        :return:
        """
        self.sub(text, level=1)

    def text(self, text: str):
        """
        Adds a text to the log

        :param text: The text to add to the log
        :return:
        """
        if not isinstance(text, str):
            text = str(text)
        for element in self.forward_targets.values():
            element.text(text)
        lines = html.escape(text)
        lines = lines.split("\n")
        for index, text in enumerate(lines):
            self._add_html(f'{text}<br>\n')
            if index == len(lines) - 1:
                self._add_md(f"{text}")
            else:
                self._add_md(f"{text}\\")
            self._add_txt(text)
        self.clip_logs()

    def line_break(self):
        """
        Inserts a simple line break
        """
        self._add_html("<br>")
        self._add_txt(" ", md=True)

    def page_break(self):
        """
        Inserts a page break
        """
        self._add_html('<div style="break-after:page"></div>')
        self._add_txt(
            f"\n{'_' * 40}\n",
            md=True)

    def sub(self, text: str, level: int = 2):
        """
        Adds a sub title to the log

        :param text: The text to add to the log
        :param level: The title level (0..5)
        :return: Self
        """
        assert 0 <= level <= 5
        for element in self.forward_targets.values():
            element.sub(text)
        md_level = "#" * level
        escaped_lines = html.escape(text)
        for cur_row in escaped_lines.split("\n"):
            self._add_html(f'<h{level}>{cur_row}</h{level}>\n')
        self._add_md(f"{md_level} {text}")
        if self._add_txt(text) and level <= 4:
            character = "=" if level < 2 else "-"
            self._add_txt(character * len(text))
        self._add_txt("")
        self.clip_logs()
        return self

    def sub_x3(self, text: str):
        """
        Adds a sub title to the log

        :param text: The text to add to the log
        :return:
        """
        self.sub(text, level=3)

    def sub_x4(self, text: str):
        """
        Adds a sub title to the log

        :param text: The text to add to the log
        :return:
        """
        self.sub(text, level=4)

    def sub_test(self, text: str):
        """
        Adds a subtest section to the log

        :param text: The text to add to the log
        :return:
        """
        self.sub(text, level=4)

    def md(self, text: str, exclude_targets: set[str] | None = None):
        """
        Adds a markdown section.

        Requires the Markdown package to be installed.

        :param text: The text to parse
        :param exclude_targets: Defines the target to exclude
        """
        if exclude_targets is None:
            exclude_targets = set()
        for element in self.forward_targets.values():
            element.md(text)
        import markdown
        parsed = markdown.markdown(text)
        if MD not in exclude_targets:
            self._add_md(text + "\n")
        if HTML not in exclude_targets:
            self._add_html(parsed + "\n")
        if TXT not in exclude_targets:
            self._add_txt(text)
        self.clip_logs()

    def html(self, code: str):
        """
        Adds a html section. (only to targets supporting html)

        :param code: The html code to parse
        """
        for element in self.forward_targets.values():
            element.html(code)
        self._add_md(code)
        self._add_html(code + "\n")
        self.clip_logs()

    def code(self, code: str):
        """
        Adds code to the log
        :param code: The code to execute
        """
        for element in self.forward_targets.values():
            element.code(code)
        escaped_code = html.escape(code).replace("\n", "<br>")
        self._add_html(f'Code<br><table class="source_code"\n>'
                       f'<tr><td style="padding: 5px;" align="left">\n'
                       f'<code>{escaped_code}</code>\n'
                       f'</td></tr></table><br><br>\n')
        self._add_md(f"```\n{code}\n```")
        self._add_txt(code)
        self.clip_logs()

    @staticmethod
    def _encode_html(text: str) -> str:
        """
        Escaped text to html compatible text

        :param text: The original unicode text
        :return: The escaped text
        """
        escaped = html.escape(text)
        res = escaped.encode('ascii', 'xmlcharrefreplace')
        return res.decode("utf-8")

    def _log_advanced(self, text, level: LogLevel):
        """
        Detects tables and other objects in a log and pretty prints the tables
        while keeping the other log data intact

        :param text: The log text
        :param level: The log level
        """
        lines = text.split("\n")
        common_block = ""
        cur_table = None
        for line in lines:
            if line.startswith(TABLE_PIPE):
                if len(common_block) > 0:
                    self.log_text(common_block, level=level)
                    common_block = ""
                if cur_table is None:
                    cur_table = []
                elements = [element.lstrip(" ").rstrip(" ") for element in
                            line.split("|")]
                if len(elements) > 2:
                    elements = elements[1:-1]
                cur_table.append(elements)
            else:
                # when back to normal mode visualize current in-progress element
                if cur_table is not None:
                    self.table(cur_table)
                    cur_table = None
                common_block += line + "\n"
        if len(common_block) > 0:
            self.log_text(common_block, level=level)

    def log_text(self, *args: Any, level: LogLevel | str = LogLevel.INFO,
                 detect_objects: bool = False,
                 space: str = " "):
        """
        Adds a log text to the log

        :param args: The text arguments to add to the log
        :param level: The importance / category of the log entry
        :param detect_objects: Defines if special objects such as tables shall
            be detected and printed beautiful
        :param space: The character or text to be used for spaces
        :return:
        """
        if isinstance(level, str):
            level = LogLevel(level)
        elements = [str(element) for element in args]
        text = space.join(elements)
        if detect_objects and TABLE_PIPE in text:
            self._log_advanced(text, level)
            return
        if text is None:
            text = "None"
        if not isinstance(text, str):
            text = str(text)
        for element in self.forward_targets.values():
            element.log_text(text, level=level)
        escaped_text = self._encode_html(text)
        self._add_html(
            f'<p class="logtext">{self._html_linebreaks(escaped_text)}</p>'
            f'<br>\n')
        if MD in self.logs and len(self.logs[MD]) > 0:
            last_md_log: str = self.logs[MD][-1].decode("utf-8")
            if last_md_log.endswith("```\n"):
                self._add_md(f"{text}\n```")
        else:
            self._add_md(f"```\n{text}\n```")
        self._add_txt(text)
        self.clip_logs()

    def info(self, *args, **kwargs) -> VisualLogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.log_text("[INFO]    ", *args, **kwargs)
        return self

    def debug(self, *args, **kwargs) -> VisualLogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.log_text("[DEBUG]   ", *args, **kwargs)
        return self

    def warning(self, *args, **kwargs) -> VisualLogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.log_text("[WARNING] ", *args, **kwargs)
        return self

    def error(self, *args, **kwargs) -> VisualLogBuilder:
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.log_text("[ERROR]   ", *args, **kwargs)
        return self

    def critical(self, *args, **kwargs) -> VisualLogBuilder:
        """
        Logs a critical error

        :param args: The elements to log. Will be separated by space.
        :param kwargs: Keyword arguments
        """
        self.log_text("[CRITICAL]", *args, **kwargs)
        return self

    def log_timestamp(self, prefix: str = "", postfix: str = ""):
        """
        Logs a timestamp to the log

        :param prefix: The text before the timestamp
        :param postfix: The text after the timestamp
        :return:
        """
        from datetime import datetime
        dt_object = datetime.now()
        cur_time = f"{str(dt_object.date())} {str(dt_object.time())}"
        elements = [cur_time]
        if len(prefix) > 0:
            elements.insert(0, prefix)
        if len(postfix) > 0:
            elements.append(postfix)
        self.log_text("".join(elements))

    def get_statistics(self) -> dict:
        """
        Returns statistics about the log

        :return: A dictionary with statistics about the log such as
            - totalUpdateCount - How often was the log updated?
            - updatesPerSecond - How often was the log updated per second
            - upTime - How long is the log being updated?
        """
        return {"totalUpdateCount": self._total_update_counter,
                "updatesPerSecond": self._update_rate,
                "upTime": time.time() - self.log.start_time}

    def log_statistics(self):
        """
        Adds statistics about the VisualLog as table to the log
        """
        self.table([["Updates", f"{self._total_update_counter} total updates"],
                    ["Effective lps",
                     f"{self._update_rate:0.2f} updates per second"],
                    ["Uptime",
                     f"{time.time() - self.log.start_time:0.2f} seconds"]],
                   index=True)

    def df(self, df: pd.DataFrame, name: str | None = None, index: bool = True):
        """
        Adds a dataframe to the log

        :param name: The dataframe's name
        :param df: The data frame
        :param index: Defines if the index shall be printed
        """
        if name is None:
            name = "dataframe"
        for element in self.forward_targets.values():
            element.df(name=name, df=df, index=index)
        if self.log.use_pretty_html_table:
            try:
                import pretty_html_table
                html_code = \
                    pretty_html_table.build_table(df,
                                                  self.log.html_table_style,
                                                  index=index)
            except ModuleNotFoundError:  # pragma: no-cover
                html_code = df.to_html(index=index)
        else:
            html_code = df.to_html(index=index)
        self._add_html(html_code + "\n")
        if self.log.use_tabulate:
            try:
                import tabulate
                md_table = df.to_markdown(index=index,
                                          tablefmt=self.log.md_table_format)
                self._add_md(md_table)
                self._add_txt(
                    df.to_markdown(index=index,
                                   tablefmt=self.log.txt_table_format) + "\n")
                return
            except ModuleNotFoundError:  # pragma: no-cover
                pass
        else:
            string_table = df.to_string(index=index) + "\n"
            if self.log.markdown_html:
                self._add_md(html_code)
            else:
                self._add_md(string_table)
            self._add_txt(string_table)
        self.log.clip_logs()

    def figure(self, figure: plt.Figure | plt.Axes | Figure | Plot,
               name: str | None = None,
               alt_text: str | None = None,
               _out_image_data: io.IOBase | None = None):
        """
        Adds a figure to the log

        :param name: The figure's name
        :param figure: The figure to log
        :param alt_text: An alternative text to display if the figure can
            not be displayed.
        :param _out_image_data: Receives the image data if provided (for
            debugging and assertion purposes)
        """
        if name is None:
            name = "figure"
        if not self.log.log_images and _out_image_data is None:
            return
        if isinstance(figure, (Figure, Plot)):
            image = figure.render()
            self.image(image, name, alt_text=alt_text)
            if _out_image_data is not None:
                _out_image_data.write(
                    image.encode(filetype=self.log.image_format,
                                 quality=self.log.image_quality))
            return
        if not isinstance(figure, plt.Figure):
            figure = figure.figure
        image_data = MPHelper.figure_to_png(figure, transparent=False)
        if _out_image_data is not None:
            _out_image_data.write(image_data)
        self.image(image_data, name, alt_text=alt_text)

    def pyplot(self) -> "PyPlotLogContext":
        """
        Opens a matplotlib context to add a figure directly to the plot.

        Also takes care off that no other thread is using matplotlib so you
        can safely plot using this function and matplotlib from multiple
        threads at once.

        ..  code-block:

            with vl.pyplot() as plt:
                figure = plt.figure(figsize=(8,4))
                plt.imshow(some_image_matrix)
        """
        from scistag.logstag.visual_log.pyplot_log_context import \
            PyPlotLogContext
        log_context = PyPlotLogContext(self)
        return log_context

    def log_dict(self, dict_or_list: dict | list):
        """
        Logs a dictionary or a list.

        The data needs to be JSON compatible so can contain further nested
        diotionaries, lists, floats, booleans or integers but no more
        complex types.

        :param dict_or_list: The dictionary or list
        """
        from scistag.common.dict_helper import dict_to_bullet_list
        dict_tree = dict_to_bullet_list(dict_or_list, level=0, bold=True)
        self.md(dict_tree, exclude_targets={'txt'})
        if self.log.txt_export:
            dict_tree_txt = dict_to_bullet_list(dict_or_list, level=0,
                                                bold=False)
            self._add_txt(dict_tree_txt)

    def log_list(self, list_data: list):
        """
        Logs a list (just for convenience), forwards to log_dict.

        The data needs to be JSON compatible so can contain further nested
        diotionaries, lists, floats, booleans or integers but no more
        complex types.

        :param list_data: The list to log
        """
        self.log_dict(list_data)

    @staticmethod
    def get_hashed_filename(name):
        """
        Returns a hashed filename for name to be store it with a fixed size
        on disk

        :param name: The file's name
        :return: The hash name to be used as filename
        """
        hashed_name = hashlib.md5(name.encode('utf-8')).hexdigest()
        return hashed_name

    @staticmethod
    def _html_linebreaks(text: str) -> str:
        """
        Replaces linebreaks through html linebreaks

        :param text: The original text
        :return: The text with html linebreaks
        """
        return text.replace("\n\r", "\n").replace("\n", "<br>")

    def _add_html(self, html_code: str):
        """
        The HTML code to add

        :param html_code: The html code
        :return: True if txt logging is enabled
        """
        self.log.write_html(html_code)

    def _add_md(self, md_code: str, no_break: bool = False):
        """
        The markdown code to add

        :param md_code: The markdown code
        :param no_break: If defined no line break will be added
        :return: True if txt logging is enabled
        """
        self.log.write_md(md_code, no_break=no_break)

    def _add_txt(self, txt_code: str, console: bool = True, md: bool = False):
        """
        Adds text code to the txt / console log

        :param txt_code: The text to add
        :param console: Defines if the text shall also be added ot the
            console's log (as it's mostly identical). True by default.
        :param md: Defines if the text shall be added to markdown as well
        :return: True if txt logging is enabled
        """
        return self.log.write_txt(txt_code, console, md)

    def clip_logs(self):
        """
        Clips the logging files (e.g. if they are limited in length)
        """
        self.log.clip_logs()

    def get_temp_path(self, relative: str | None = None) -> str:
        """
        Returns the temporary file path. The data will be wiped upon the call
        of finalize.

        :param relative: A relative path which can be passed and automatically
            gets concatenated.
        :return: The path or combined path
        """
        return self.log.get_temp_path(relative)
