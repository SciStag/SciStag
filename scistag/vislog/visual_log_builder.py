"""
Defines the class :class:`VisualLogBuilder` which is the main interface for
adding data in a VisualLog.
"""

from __future__ import annotations

import types
from typing import Any, TYPE_CHECKING, Union
import io

import html

import hashlib

import filetype
import numpy as np
from pydantic import BaseModel

from scistag.imagestag import Image, Size2D
from scistag.vislog.log_elements import HTMLCode
from scistag.vislog.options import LogOptions

from scistag.vislog.visual_log import VisualLog, HTML
from scistag.plotstag import Figure, Plot, MPHelper

if TYPE_CHECKING:
    import pandas as pd
    from matplotlib import pyplot as plt
    from scistag.vislog.sessions.page_session import PageSession
    from scistag.vislog.common.page_update_context import PageUpdateContext
    from scistag.vislog.extensions.pyplot_log_context import PyPlotLogContext
    from scistag.vislog.extensions.markdown_logger import MarkdownLogger
    from scistag.vislog.extensions.pandas_logger import PandasLogger
    from scistag.vislog.extensions.numpy_logger import NumpyLogger
    from scistag.vislog.extensions.cell_logger import CellLogger
    from scistag.vislog.extensions.collection_logger import CollectionLogger
    from scistag.vislog.extensions.widget_logger import WidgetLogger
    from scistag.vislog.extensions.alignment_logger import AlignmentLogger

LogableContent = Union[
    str,
    float,
    int,
    bool,
    np.ndarray,
    "pd.DataFrame",
    "pd.Series",
    list,
    dict,
    Image,
    Figure,
]
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

    def __init__(
            self, log: "VisualLog", page_session: Union["PageSession", None] = None
    ):
        """
        :param log: The log to which the content shall be added.
        """
        self.target_log: "VisualLog" = log
        self.page_session = page_session
        """
        Defines the target page which will store this builder's data
        """
        if self.page_session is None:
            self.page_session = log.default_page
        self._file_dependencies = []
        """
        A list of files which were used to build the current log. When ever
        any of these files changes the log should be rebuild.
        """
        "The main logging target"
        from .extensions.test_helper import TestHelper

        self.test = TestHelper(self)
        """
        Helper class for adding regression tests to the log.
        """
        from .extensions.image_logger import ImageLogger

        self.image = ImageLogger(self)
        """
        Helper object for adding images to the log
        
        Can also be called directly to add a simple image to the log.
        """
        from .extensions.table_logger import TableLogger

        self.table = TableLogger(self)
        """
        Helper class for adding tables to the log.
        
        Can also be called directly to add a simple table to the log.
        """
        from .extensions.time_logger import TimeLogger

        self.time = TimeLogger(self)
        """
        Helper class for time measuring and logging times to the log
        """
        from .extensions.basic_logger import BasicLogger

        self.log = BasicLogger(self)
        self._md: Union["MarkdownLogger", None] = None
        """
        Markdown extension
        """
        self._pd: Union["PandasLogger", None] = None
        """
        Pandas extension for logging DataFrames and DataSeries
        """
        self._np: Union["NumpyLogger", None] = None
        """
        Numpy extension for logging numpy matrices and vectors 
        """
        self._collection: Union["CollectionLogger", None] = None
        """
        Extension to log lists and dictionaries
        """
        self._cell: Union["CellLogger", None] = None
        """
        Extension to add replaceable, dynamic content cells
        """
        self._widget: Union["WidgetLogger", None] = None
        """
        Extension to add visual, interactive components 
        """
        self._align: Union["AlignmentLogger", None] = None
        """
        Extension to align elements 
        """
        self.options: LogOptions = log.options.copy(deep=True)
        """
        Defines the builder's options
        """

    def build(self):
        """
        Is called when the body of the log shall be build or rebuild.

        This is usually the function you want to override to implement your
        own page builder.
        """
        for key, value in self.__class__.__dict__.items():
            attr = getattr(self, key)
            if isinstance(attr, types.MethodType):
                if "__log_cell" in attr.__dict__:
                    cell_config = attr.__dict__["__log_cell"]
                    new_cell = self.cell.add(
                        on_build=attr, **cell_config, _builder_method=attr
                    )

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
        self.page_session.clear()

    def embed(self, page: PageSession):
        """
        Embeds another VisualLog's content into this one

        :param page: The source log page to embed
        """
        self.page_session.embed(page)

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

    def add(self, content: LogableContent, br: bool = False) -> VisualLogBuilder:
        """
        Adds the provided content to the log.

        Supports a large variety of types. All supported types can also
        easily be embedded into tables and divs via the provided add_row
        and add_col methods.

        Note that in different to the method :meth:`text` adding a text will not
        result in a linebreak by default for a single row text element.

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
        :param br: Defines if the element shall be followed by a linebreak
            (if supported), false by default.
        :return: The builder
        """
        # pandas content frame
        import pandas as pd

        if hasattr(content, "to_html") and not isinstance(
                content, (pd.DataFrame, pd.Series)
        ):
            self.html(content.to_html())
            return self
        if hasattr(content, "to_md"):
            self.md(content.to_md())
            return self
        if isinstance(content, bytes):
            try:
                ft = filetype.guess(content)
            except TypeError:
                raise ValueError(f"Data type could not be detected")
            from scistag.imagestag.image import SUPPORTED_IMAGE_FILETYPES

            if ft is not None and ft.extension in SUPPORTED_IMAGE_FILETYPES:
                self.image(content)
                return self
            else:
                raise ValueError(f"Data of filetype {ft} not supported")
        # image
        if isinstance(content, Image):
            self.image(content, br=br)
            return self
        # figure
        if isinstance(content, Figure):
            self.figure(content, br=br)
            return self

        if isinstance(content, (pd.DataFrame, pd.Series)):
            self.pd(content)
            return self
        # numpy array
        if isinstance(content, np.ndarray):
            self.np(content, br=br)
            return self
        if isinstance(content, (str, int, float)):
            self.text(content, br=br)
            return self
            # dict or list
        if isinstance(content, (list, dict)):
            self.collection.add(content)
            return self
        self.text(str(content), br=br)
        if content is None or not isinstance(content, bytes):
            raise TypeError("Data type not supported")
        return self

    def title(self, text: str) -> VisualLogBuilder:
        """
        Adds a title to the log

        :param text: The title's text
        :return: The builder
        """
        self.sub(text, level=1)
        return self

    def text(self, text: str, br: bool = True) -> VisualLogBuilder:
        """
        Adds a text to the log

        :param text: The text to add to the log
        :param br: Defines if a linebreak shall be printed in case of a single
            row text element.
        :return: The builder
        """
        if not isinstance(text, str):
            text = str(text)
        lines = html.escape(text)
        lines = lines.split("\n")
        if br:
            for index, text in enumerate(lines):
                self.add_html(f"{text}<br>\n")
                if index == len(lines) - 1:
                    self.add_md(f"{text}\n")
                else:
                    self.add_md(f"{text}\\")
                self.add_txt(text)
        else:  # no line break
            for index, text in enumerate(lines):
                if index == len(lines) - 1:
                    self.add_html(f"{text}")
                    self.add_md(f"{text}")
                    self.add_md(f"{text}")
                else:  # only break if there is really an explicit line break
                    self.add_html(f"{text}<br>\n")
                    self.add_md(f"{text}\n")
                    self.add_md(f"{text}\\")
                self.add_txt(text)
        self.handle_modified()
        return self

    def link(self, text: str, link: str, br: bool = False) -> VisualLogBuilder:
        """
        Adds a hyperlink to the log

        :param text: The text to add to the log
        :param link: The link target
        :param br: Defines if a linebreak shall be inserted after the link
        :return: The builder
        """
        if not isinstance(text, str):
            text = str(text)
        lines = html.escape(text)
        lines = lines.split("\n")
        for index, text in enumerate(lines):
            last_line = index == len(lines) - 1
            do_break = br or not last_line
            break_char = "<br>\n" if do_break else ""
            self.add_html(f'<a href="{link}">{text}</a>{break_char}')
            if index == len(lines) - 1:
                self.add_md(f"[{text}]({link})")
            else:
                self.add_md(f"{text}\\", no_break=not do_break)
            self.add_txt(text)
        self.handle_modified()
        return self

    def br(self, repetition=1) -> VisualLogBuilder:
        """
        Inserts a simple line break

        :param repetition: The count of linebreaks
        :return: The builder
        """
        self.add_html("<br>" * repetition)
        self.add_txt(" ", md=True)
        return self

    def page_break(self) -> VisualLogBuilder:
        """
        Inserts a page break

        :return: The builder
        """
        self.add_html('<div style="break-after:page"></div>')
        self.add_txt(f"\n{'_' * 40}\n", md=True)
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
            self.add_html(f"<h{level}>{cur_row}</h{level}>\n")
        self.add_md(f"{md_level} {text}")
        if self.add_txt(text) and level <= 4:
            character = "=" if level < 2 else "-"
            self.add_txt(character * len(text))
        self.add_txt("")
        self.handle_modified()
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

    def html(self, code: str | HTMLCode) -> VisualLogBuilder:
        """
        Adds a html section. (only to targets supporting html)

        :param code: The html code to parse
        """
        if isinstance(code, HTMLCode):
            code = HTMLCode.to_html()
        self.add_md(code)
        self.add_html(code + "\n")
        self.handle_modified()
        return self

    @property
    def md(self) -> "MarkdownLogger":
        """
        Methods to add markdown content
        """
        from .extensions.markdown_logger import MarkdownLogger

        if self._md is None:
            self._md = MarkdownLogger(self)
        return self._md

    @property
    def pd(self) -> "PandasLogger":
        """
        Methods to add Pandas content such as DataFrames and DataSeries
        """
        from .extensions.pandas_logger import PandasLogger

        if self._pd is None:
            self._pd = PandasLogger(self)
        return self._pd

    @property
    def np(self) -> "NumpyLogger":
        """
        Methods to add Numpy data to the log such as matrices and vectors
        """
        from .extensions.numpy_logger import NumpyLogger

        if self._np is None:
            self._np = NumpyLogger(self)
        return self._np

    @property
    def collection(self) -> "CollectionLogger":
        """
        Methods to add dictionaries and lists to the log
        """
        from .extensions.collection_logger import CollectionLogger

        if self._collection is None:
            self._collection = CollectionLogger(self)
        return self._collection

    @property
    def cell(self) -> "CellLogger":
        """
        Methods to add dynamic content regions to the log
        """
        from .extensions.cell_logger import CellLogger

        if self._cell is None:
            self._cell = CellLogger(self)
        return self._cell

    @property
    def widget(self) -> "WidgetLogger":
        """
        Methods to add interactive widgets to the log
        """
        from .extensions.widget_logger import WidgetLogger

        if self._widget is None:
            self._widget = WidgetLogger(self)
        return self._widget

    @property
    def align(self) -> "AlignmentLogger":
        """
        Methods to align elements, e.g. to the right or to the center
        """
        from .extensions.alignment_logger import AlignmentLogger

        if self._align is None:
            self._align = AlignmentLogger(self)
        return self._align

    def code(self, code: str) -> VisualLogBuilder:
        """
        Adds code to the log

        :param code: The code to execute
        :return: The builder
        """
        escaped_code = html.escape(code).replace("\n", "<br>")
        self.add_html(
            f'Code<br><table class="source_code"\n>'
            f'<tr><td style="padding: 5px;" align="left">\n'
            f"<code>{escaped_code}</code>\n"
            f"</td></tr></table><br><br>\n"
        )
        self.add_md(f"```\n{code}\n```")
        self.add_txt(code)
        self.handle_modified()
        return self

    @staticmethod
    def encode_html(text: str) -> str:
        """
        Escaped text to html compatible text

        :param text: The original unicode text
        :return: The escaped text
        """
        escaped = html.escape(text)
        res = escaped.encode("ascii", "xmlcharrefreplace")
        return res.decode("utf-8")

    def log_statistics(self):
        """
        Adds statistics about the VisualLog as table to the log
        """
        statistics = self.target_log.get_statistics()
        self.table(
            [
                ["Updates", f"{statistics.update_counter} " f"total updates"],
                ["Effective lps", f"{statistics.update_rate:0.2f} updates per second"],
                ["Uptime", f"{statistics.uptime:0.2f} seconds"],
            ],
            index=True,
        )

    def figure(
            self,
            figure: Union["plt.Figure", "plt.Axes", Figure, Plot],
            name: str | None = None,
            alt_text: str | None = None,
            _out_image_data: io.IOBase | None = None,
            br: bool = False,
    ):
        """
        Adds a figure to the log

        :param name: The figure's name
        :param figure: The figure to log
        :param alt_text: An alternative text to display if the figure can
            not be displayed.
        :param _out_image_data: Receives the image data if provided (for
            debugging and assertion purposes)
        :param br: Defines if the figure shall be followed by a linebreak
        """
        if name is None:
            name = "figure"
        if not self.target_log.log_images and _out_image_data is None:
            return
        if isinstance(figure, (Figure, Plot)):
            image = figure.render()
            self.image(image, name, alt_text=alt_text, br=br)
            if _out_image_data is not None:
                _out_image_data.write(
                    image.encode(
                        filetype=self.target_log.image_format,
                        quality=self.target_log.image_quality,
                    )
                )
            return
        import matplotlib.pyplot as plt

        if not isinstance(figure, plt.Figure):
            figure = figure.figure
        image_data = MPHelper.figure_to_png(figure, transparent=False)
        if _out_image_data is not None:
            _out_image_data.write(image_data)
        self.image(image_data, name, alt_text=alt_text, br=br)

    def pyplot(
            self,
            assertion_name: str | None = None,
            assertion_hash: str | None = None,
            br: bool = False,
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
        :param br: Defines if the figure shall be followed by a linebreak.

        ..  code-block:

            with vl.pyplot() as plt:
                figure = plt.figure(figsize=(8,4))
                plt.imshow(some_image_matrix)


        """
        from scistag.vislog.extensions.pyplot_log_context import PyPlotLogContext

        log_context = PyPlotLogContext(
            self, assertion_name=assertion_name, assertion_hash=assertion_hash, br=br
        )
        return log_context

    @staticmethod
    def get_hashed_filename(name):
        """
        Returns a hashed filename for name to be store it with a fixed size
        on disk

        :param name: The file's name
        :return: The hash name to be used as filename
        """
        hashed_name = hashlib.md5(name.encode("utf-8")).hexdigest()
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
        self.page_session.write_html(html_code)

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
        self.flush()
        if HTML not in self.page_session.log_formats:
            raise ValueError("At the moment only HTML backup is supported")
        return VisualLogBackup(data=self.page_session.get_body(HTML))

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
        self.page_session.write_md(md_code, no_break=no_break)

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
        return self.page_session.write_txt(txt_code, console, md)

    def handle_modified(self):
        """
        Is called when a new block of content has been inserted
        """
        self.page_session.handle_modified()

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
        return self.page_session.reserve_unique_name(name)

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

    def begin_update(self) -> "PageUpdateContext":
        """
        Can be called at the beginning of a larger update block, e.g. if a page
        is completely cleared and re-built to prevent page flickering.

        Will automatically created a backup of the page's previous state and will
        return this update until end_update is called as often as begin_update.

        A PageUpdateContext can be used via `with self.begin_update()` to automatically
        call end_update once the content block is left.
        """
        self.page_session.begin_update()

    def end_update(self):
        """
        Ends the update mode
        """
        self.page_session.end_update()
