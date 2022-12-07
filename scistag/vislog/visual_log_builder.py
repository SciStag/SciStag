"""
Defines the class :class:`VisualLogBuilder` which is the main interface for
adding data in a VisualLog.
"""

from __future__ import annotations

from typing import Optional, Any, TYPE_CHECKING, Union
import io

import html

import hashlib

import filetype
import numpy as np
from pydantic import BaseModel

from scistag.imagestag import Image, Canvas, PixelFormat, Size2D

from scistag.vislog.visual_log import VisualLog, MD, TXT, HTML, \
    TABLE_PIPE
from scistag.plotstag import Figure, Plot, MPHelper

MAX_NP_ARRAY_SIZE = 100

if TYPE_CHECKING:
    from scistag.vislog.pyplot_log_context import PyPlotLogContext
    from scistag.vislog.visual_log_markdown_builder import \
        VisualMarkdownBuilderExtension
    from matplotlib import pyplot as plt
    import pandas as pd

LogableContent = Union[str, float, int, bool, np.ndarray,
                       "pd.DataFrame", "pd.Series", list, dict, Image, Figure]
"""
Definition of all types which can be logged via `add` or provided as content
for tables, lists and divs.
"""


class VisualLogBackup(BaseModel):
    """
    Contains the backup of a log and all necessary data to integrate it into
    another log.
    """
    data: bytes
    "The logs html representation"


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
        self.target_log: "VisualLog" = log
        self._file_dependencies = []
        """
        A list of files which were used to build the current log. When ever
        any of these files changes the log should be rebuild.
        """
        "The main logging target"
        from .visual_log_test_helper import VisualLogTestHelper
        self.test = VisualLogTestHelper(self)
        """
        Helper class for adding regression tests to the log.
        """
        from .visual_image_logger import VisualImageLogger
        self.image = VisualImageLogger(self)
        """
        Helper object for adding images to the log
        
        Can also be called directly to add a simple image to the log.
        """
        from .visual_log_table_builder import VisualLogTableBuilderExtension
        self.table = VisualLogTableBuilderExtension(self)
        """
        Helper class for adding tables to the log.
        
        Can also be called directly to add a simple table to the log.
        """
        from .visual_time_logger import VisualLogTimeLogger
        self.time = VisualLogTimeLogger(self)
        """
        Helper class for time measuring and logging times to the log
        """
        from .visual_log_basic_logger import VisualLogBasicLogger
        self.log = VisualLogBasicLogger(self)
        from .visual_log_markdown_builder import VisualMarkdownBuilderExtension
        self._md: VisualMarkdownBuilderExtension | None = None
        """
        Markdown extension for VisualLog
        """

    def build(self):
        """
        Is called when the body of the log shall be build or rebuild.

        This is usually the function you want to override to implement your
        own page builder.
        """
        pass

    def build_page(self):
        """
        Builds the whole page including header, footers and other sugar.

        Only overwrite this if you really want to do a more complex
        customization.
        """
        self.build_header()
        self.build()
        self.build_footer()

    def build_header(self):
        """
        Called to build the page's header and before the body
        """
        pass

    def build_footer(self):
        """
        Called to build the page's footer and after the body
        """
        pass

    @property
    def max_fig_size(self) -> Size2D:
        """
        The maximum figure size in pixels
        """
        return self.target_log.max_fig_size

    def clear(self):
        """
        Clears the whole log (excluding headers and footers)
        """
        self.target_log.clear()

    def embed(self, log: VisualLog):
        """
        Embeds another VisualLog's content into this one

        :param log: The source log
        """
        self.target_log.embed(log)

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

    def add(self, content: LogableContent) -> VisualLogBuilder:
        """
        Adds the provided content to the log.

        Supports a large variety of types. All supported types can also
        easily be embedded into tables and divs via the provided add_row
        and add_col methods.

        :param content: The data to be logged.

            Currently supported types are
            * bytes:
                * png, jpg, bmp or gif byte strings
            * Image(s) - see :class:`Image
            * Figure(s) - :class:`Figure`
            * Pandas DataFrame(s) and Series
            * Nunpy Arrays
            * Common Python types such as dicts and dists, strings, floats and
                ints.
        :return: The builder
        """
        if isinstance(content, bytes):
            try:
                ft = filetype.guess(content)
            except TypeError:
                raise ValueError(f"Data type could not be detected")
            from scistag.imagestag.image import SUPPORTED_IMAGE_FILETYPES
            if ft.extension in SUPPORTED_IMAGE_FILETYPES:
                self.image(content)
                return
            else:
                raise ValueError(f"Data of filetype {ft} not supported")
        # image
        if isinstance(content, Image):
            self.image(content)
            return self
        # figure
        if isinstance(content, Figure):
            self.figure(content)
            return self
        # pandas content frame
        import pandas as pd
        if isinstance(content, (pd.DataFrame, pd.Series)):
            self.df(content)
            return self
        # numpy array
        if isinstance(content, np.ndarray):
            self.np(content)
            return self
        if isinstance(content, (str, int, float)):
            self.text(content)
            return self
            # dict or list
        if isinstance(content, (list, dict)):
            self.log_dict(content)
            return self
        self.log(str(content))
        if content is None or not isinstance(content, bytes):
            raise NotImplementedError("Data type not supported")
        return self

    def title(self, text: str) -> VisualLogBuilder:
        """
        Adds a title to the log

        :param text: The title's text
        :return: The builder
        """
        self.sub(text, level=1)
        return self

    def text(self, text: str) -> VisualLogBuilder:
        """
        Adds a text to the log

        :param text: The text to add to the log
        :return: The builder
        """
        if not isinstance(text, str):
            text = str(text)
        lines = html.escape(text)
        lines = lines.split("\n")
        for index, text in enumerate(lines):
            self.add_html(f'{text}<br>\n')
            if index == len(lines) - 1:
                self.add_md(f"{text}\n")
            else:
                self.add_md(f"{text}\\")
            self.add_txt(text)
        self.clip_logs()
        return self

    def link(self, text: str, link: str) -> VisualLogBuilder:
        """
        Adds a hyperlink to the log

        :param text: The text to add to the log
        :param link: The link target
        :return: The builder
        """
        if not isinstance(text, str):
            text = str(text)
        lines = html.escape(text)
        lines = lines.split("\n")
        for index, text in enumerate(lines):
            self.add_html(f'<a href="{link}">{text}</a><br>\n')
            if index == len(lines) - 1:
                self.add_md(f"[{text}]({link})")
            else:
                self.add_md(f"{text}\\")
            self.add_txt(text)
        self.clip_logs()
        return self

    def br(self) -> VisualLogBuilder:
        """
        Inserts a simple line break

        :return: The builder
        """
        self.add_html("<br>")
        self.add_txt(" ", md=True)
        return self

    def page_break(self) -> VisualLogBuilder:
        """
        Inserts a page break

        :return: The builder
        """
        self.add_html('<div style="break-after:page"></div>')
        self.add_txt(
            f"\n{'_' * 40}\n",
            md=True)
        return self

    def sub(self, text: str, level: int = 2) -> VisualLogBuilder:
        """
        Adds a sub title to the log

        :param text: The text to add to the log
        :param level: The title level (0..5)
        :return: The builder
        """
        assert 0 <= level <= 5
        md_level = "#" * level
        escaped_lines = html.escape(text)
        for cur_row in escaped_lines.split("\n"):
            self.add_html(f'<h{level}>{cur_row}</h{level}>\n')
        self.add_md(f"{md_level} {text}")
        if self.add_txt(text) and level <= 4:
            character = "=" if level < 2 else "-"
            self.add_txt(character * len(text))
        self.add_txt("")
        self.clip_logs()
        return self

    def sub_x3(self, text: str) -> VisualLogBuilder:
        """
        Adds a subtitle to the log

        :param text: The text to add to the log
        :return: The builder
        """
        self.sub(text, level=3)
        return self

    def sub_x4(self, text: str) -> VisualLogBuilder:
        """
        Adds a subtitle to the log

        :param text: The text to add to the log
        :return: The builder
        """
        self.sub(text, level=4)
        return self

    def sub_test(self, text: str) -> VisualLogBuilder:
        """
        Adds a subtest section to the log

        :param text: The text to add to the log
        :return: The builder
        """
        self.sub(text, level=4)
        return self

    def hr(self) -> VisualLogBuilder:
        """
        Adds a horizontal rule to the document

        :return: The builder
        """
        self.add_html("<hr>")
        self.add_txt("---", md=True)
        return self

    def html(self, code: str) -> VisualLogBuilder:
        """
        Adds a html section. (only to targets supporting html)

        :param code: The html code to parse
        """
        self.add_md(code)
        self.add_html(code + "\n")
        self.clip_logs()
        return self

    @property
    def md(self) -> "VisualMarkdownBuilderExtension":
        """
        Methods to add markdown content
        """
        from .visual_log_markdown_builder import VisualMarkdownBuilderExtension
        if self._md is None:
            self._md = VisualMarkdownBuilderExtension(self)
        return self._md

    def code(self, code: str) -> VisualLogBuilder:
        """
        Adds code to the log

        :param code: The code to execute
        :return: The builder
        """
        escaped_code = html.escape(code).replace("\n", "<br>")
        self.add_html(f'Code<br><table class="source_code"\n>'
                      f'<tr><td style="padding: 5px;" align="left">\n'
                      f'<code>{escaped_code}</code>\n'
                      f'</td></tr></table><br><br>\n')
        self.add_md(f"```\n{code}\n```")
        self.add_txt(code)
        self.clip_logs()
        return self

    @staticmethod
    def encode_html(text: str) -> str:
        """
        Escaped text to html compatible text

        :param text: The original unicode text
        :return: The escaped text
        """
        escaped = html.escape(text)
        res = escaped.encode('ascii', 'xmlcharrefreplace')
        return res.decode("utf-8")

    def log_statistics(self):
        """
        Adds statistics about the VisualLog as table to the log
        """
        statistics = self.target_log.get_statistics()
        self.table([["Updates", f"{statistics.update_counter} "
                                f"total updates"],
                    ["Effective lps",
                     f"{statistics.update_rate:0.2f} updates per second"],
                    ["Uptime",
                     f"{statistics.uptime:0.2f} seconds"]],
                   index=True)

    def df(self, df: "pd.DataFrame", name: str | None = None,
           index: bool = True):
        """
        Adds a dataframe to the log

        :param name: The dataframe's name
        :param df: The data frame
        :param index: Defines if the index shall be printed
        """
        if name is None:
            name = "dataframe"
        if self.target_log.use_pretty_html_table:
            try:
                import pretty_html_table
                html_code = \
                    pretty_html_table. \
                        build_table(df,
                                    self.target_log.html_table_style,
                                    index=index)
            except ModuleNotFoundError:  # pragma: no-cover
                html_code = df.to_html(index=index)
        else:
            html_code = df.to_html(index=index)
        self.add_html(html_code + "\n")
        if self.target_log.use_tabulate:
            try:
                import tabulate
                md_table = \
                    df.to_markdown(index=index,
                                   tablefmt=self.target_log.md_table_format)
                self.add_md(md_table)
                self.add_txt(
                    df.to_markdown(index=index,
                                   tablefmt=self.target_log.txt_table_format) +
                    "\n")
                return
            except ModuleNotFoundError:  # pragma: no-cover
                pass
        else:
            string_table = df.to_string(index=index) + "\n"
            if self.target_log.markdown_html:
                self.add_md(html_code)
            else:
                self.add_md(string_table)
            self.add_txt(string_table)
        self.target_log.clip_logs()

    def np(self, data: np.ndarray, max_digits=2):
        """
        Adds a numpy matrix or vector to the log

        :param data: The data frame
        :param max_digits: The number of digits with which the numbers shall be
            formatted.
        """
        if len(data.shape) >= 3:
            raise ValueError("Too many dimensions")
        if len(data.shape) == 1:
            data = [[f"{round(element, max_digits)}" for element in data]]
        else:
            if (data.shape[0] > MAX_NP_ARRAY_SIZE or
                    data.shape[1] > MAX_NP_ARRAY_SIZE):
                raise ValueError("Data too large")
            data = [[f"{round(element, max_digits)}" for element in row] for row
                    in
                    data]
        self.table(data)

    def figure(self, figure: Union["plt.Figure", "plt.Axes", Figure, Plot],
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
        if not self.target_log.log_images and _out_image_data is None:
            return
        if isinstance(figure, (Figure, Plot)):
            image = figure.render()
            self.image(image, name, alt_text=alt_text)
            if _out_image_data is not None:
                _out_image_data.write(
                    image.encode(filetype=self.target_log.image_format,
                                 quality=self.target_log.image_quality))
            return
        import matplotlib.pyplot as plt
        if not isinstance(figure, plt.Figure):
            figure = figure.figure
        image_data = MPHelper.figure_to_png(figure, transparent=False)
        if _out_image_data is not None:
            _out_image_data.write(image_data)
        self.image(image_data, name, alt_text=alt_text)

    def pyplot(self,
               assertion_name: str | None = None,
               assertion_hash: str | None = None
               ) -> "PyPlotLogContext":
        """
        Opens a matplotlib context to add a figure directly to the plot.

        Also takes care off that no other thread is using matplotlib so you
        can safely plot using this function and matplotlib from multiple
        threads at once.

        :param assertion_name: If the figure shall be asserted, it's unique
            identifier.
        :param assertion_hash: If the figure shall be asserted via hash the
            hash value of its image's pixels.

        ..  code-block:

            with vl.pyplot() as plt:
                figure = plt.figure(figsize=(8,4))
                plt.imshow(some_image_matrix)


        """
        from scistag.vislog.pyplot_log_context import \
            PyPlotLogContext
        log_context = PyPlotLogContext(self,
                                       assertion_name=assertion_name,
                                       assertion_hash=assertion_hash)
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
        if self.target_log.txt_export:
            dict_tree_txt = dict_to_bullet_list(dict_or_list, level=0,
                                                bold=False)
            self.add_txt(dict_tree_txt)

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
    def html_linebreaks(text: str) -> str:
        """
        Replaces linebreaks through html linebreaks

        :param text: The original text
        :return: The text with html linebreaks
        """
        return text.replace("\n\r", "\n").replace("\n", "<br>")

    def add_html(self, html_code: str | bytes):
        """
        Adds html code directly of the HTML section of this log.

        Do not use this for logging to multiple output formats. For that
        case use :meth:`html`.

        :param html_code: The html code
        :return: True if txt logging is enabled
        """
        self.target_log.write_html(html_code)

    def create_backup(self) -> VisualLogBackup:
        """
        Creates a backup of the log's content so it can for example be
        returned from a helper process or node to the main process and
        be inserted in the main log.

        See :meth:`VisualLogBuilder.insert_backup`

        Note:
        At the moment only the HTML data can be backuped and inserted.

        :return: The backup data
        """
        if HTML not in self.target_log.log_formats:
            raise ValueError("At the moment only HTML backup is supported")
        return VisualLogBackup(data=self.target_log.get_body(HTML))

    def insert_backup(self, backup: VisualLogBackup):
        """
        Inserts another log's backup in this log

        :param backup: The backup data
        """
        self.add_html(backup.data)

    def add_md(self, md_code: str, no_break: bool = False):
        """
        Adds markdown code directly of the markdown section of this log.

        Do not use this for logging to multiple output formats. For that
        case use :meth:`md`.

        :param md_code: The markdown code
        :param no_break: If defined no line break will be added
        :return: True if txt logging is enabled
        """
        self.target_log.write_md(md_code, no_break=no_break)

    def add_txt(self, txt_code: str, console: bool = True, md: bool = False):
        """
        Adds html code directly of the text and console section of this log.

        Do not use this for logging to multiple output formats. For that
        case use :meth:`txt`.

        :param txt_code: The text to add
        :param console: Defines if the text shall also be added ot the
            console's log (as it's mostly identical). True by default.
        :param md: Defines if the text shall be added to markdown as well
        :return: True if txt logging is enabled
        """
        return self.target_log.write_txt(txt_code, console, md)

    def clip_logs(self):
        """
        Clips the logging files (e.g. if they are limited in length)
        """
        self.target_log.clip_logs()

    def get_temp_path(self, relative: str | None = None) -> str:
        """
        Returns the temporary file path. The data will be wiped upon the call
        of finalize.

        :param relative: A relative path which can be passed and automatically
            gets concatenated.
        :return: The path or combined path
        """
        return self.target_log.get_temp_path(relative)

    def reserve_unique_name(self, name: str) -> str:
        """
        Reserves a unique name within the log, e.g. to store an object to
        a unique file.

        :param name: The desired name
        :return: The effective name with which the data shall be stored
        """
        return self.target_log.reserve_unique_name(name)

    def flush(self) -> VisualLogBuilder:
        """
        Finalizes the pages so they can be dumped and/or read

        :return: The builder
        """
        self.target_log.flush()
        return self

    def add_file_dependency(self, filename: str):
        """
        Adds a file dependency to the log for automatic cache clearance and
        triggering the auto-reloader (if enabled) when an included file gets
        modified.

        :param filename: The name of the file which shall be tracked. By
            default only local files are observed.
        """
        self._file_dependencies.append(filename)
