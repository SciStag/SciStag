"""
Defines the class :class:`LogBuilder` which is the main interface for
adding data in a VisualLog.
"""

from __future__ import annotations

import os.path
import types
from typing import Any, TYPE_CHECKING, Union
import io

import html

import hashlib

import filetype
import numpy as np
from pydantic import BaseModel

import scistag
from scistag.filestag import FileStag, FilePath
from scistag.imagestag import Image, Size2D
from scistag.vislog.log_elements import HTMLCode
from scistag.vislog.options import LogOptions

from scistag.vislog.visual_log import VisualLog, HTML, MD
from scistag.plotstag import Figure, Plot, MPHelper
from .log_builder_registry import LogBuilderRegistry
from ..webstag.mime_types import MIMETYPE_MARKDOWN, MIMETYPE_HTML

if TYPE_CHECKING:
    import pandas as pd
    from matplotlib import pyplot as plt
    from scistag.vislog.sessions.page_session import PageSession
    from scistag.vislog.common.page_update_context import PageUpdateContext
    from .common.element_context import ElementContext
    from .extensions.test_helper import TestHelper
    from .extensions.pyplot_log_context import PyPlotLogContext
    from .extensions.markdown_logger import MarkdownLogger
    from .extensions.table_logger import TableLogger
    from .extensions.pandas_logger import PandasLogger
    from .extensions.numpy_logger import NumpyLogger
    from .extensions.cell_logger import CellLogger
    from .extensions.collection_logger import CollectionLogger
    from .extensions.widget_logger import WidgetLogger
    from .extensions.alignment_logger import AlignmentLogger
    from .extensions.style_context import StyleContext
    from .extensions.image_logger import ImageLogger
    from .extensions.table_logger import TableLogger
    from .extensions.time_logger import TimeLogger
    from .extensions.basic_logger import BasicLogger
    from .extensions.build_logger import BuildLogger
    from .extensions.emoji_logger import EmojiLogger
    from .extensions.service_extension import (
        LogServiceExtension,
        PublishingInfo,
    )

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


class LogBackup(BaseModel):
    """
    Contains the backup of a log and all necessary data to integrate it into
    another log.
    """

    data: bytes
    "The logs html representation"


class LogBuilder:
    """
    Defines the central element to dynamically build and update a log document.

    It provides all basic log writing functions, embeds LogBuilderExtensions for
    advanced logging and styling such as .align, .table or .image and manages
    the whole event flow, from updating dynamic cells to reacting to user interactions.
    """

    def __init__(
        self,
        log: "VisualLog",
        page_session: Union["PageSession", None] = None,
        nested: bool = False,
        params: dict | BaseModel | Any | None = None,
        **kwargs,
    ):
        """
        :param log: The log to which the content shall be added.
        :param page_session: The page session (contains the logged outputs)
        :param nested: Defines if the LogBuilder is nested within another LogBuilder's
            result and shall thus not return the header and footer.
        :param params: Additional parameters
        :param kwargs: Additional keyword arguments
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

        self._test: Union["TestHelper", None] = None
        """
        Helper class for adding regression tests to the log.
        """
        self._image: Union["ImageLogger", None] = None
        """
        Helper object for adding images to the log
        
        Can also be called directly to add a simple image to the log.
        """

        self._table: Union["TableLogger", None] = None
        """
        Helper class for adding tables to the log.
        
        Can also be called directly to add a simple table to the log.
        """

        self._time: Union["TimeLogger", None] = None
        """
        Helper class for time measuring and logging times to the log
        """
        self._emoji: Union["EmojiLogger", None] = None
        """
        Helper class for adding emojis to the log
        """
        self._log: Union["BasicLogger", None] = None
        """
        Provides methods for classical logging where you can flag each entry with
        an individual priority to highlight important and or filter unimportant
        entries. 
        """
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
        self._style: Union["StyleContext", None] = None
        """
        Extension to temporarily modify the style of the current log region or cell
        and to insert custom CSS code into the document.
        """
        self._build: Union["BuildLogger", None] = None
        """
        Extension for embedding other logs (such as LogBuilders) into the main log
        to be able to build more complex, cleanly separated solutions and to enhance the
        performance by parallelling their execution.
"""
        from scistag.vislog.extensions.service_extension import LogServiceExtension

        self.options: LogOptions = log.options.copy(deep=True)
        """
        Defines the builder's options
        """
        self._service: LogServiceExtension = LogServiceExtension(builder=self)
        """
        The service extension for hosting static files and services
        """
        self._title = self.target_log._title

        # add upload widget extension
        path = FilePath.dirname(__file__)
        self.publish(
            "visual_log.css",
            path + "/css/visual_log.css",
        )
        self.publish(
            "vl_file_upload.css",
            path + "/templates/extensions/upload/vl_file_upload.css",
        )
        self.publish(
            "vl_file_upload.js",
            path + "/templates/extensions/upload/vl_file_upload.js",
        )
        self.service.register_css("VlBaseCss", "visual_log.css")
        self.service.register_css("VlUploadWidget", "vl_file_upload.css")
        self.service.register_js("VlUploadWidget", "vl_file_upload.js")

        """The website's title"""
        self._provide_live_view()
        self.params = params if params is not None else {}
        """Defines the current set of parameters"""
        self.nested = nested
        """
        Defines if this builder object is nested within another log and shall not
        return header and footer in it's get_result() method.
        """

        self._cur_alignment_block = "left"
        """The current div alignment"""
        self._cur_alignment = "left"
        """The current text alignment"""
        self._console_size = (120, 25)
        """The console width"""

    def build(self):
        """
        Is called when the body of the log shall be build or rebuild.

        This is usually the function you want to override to implement your
        own page builder.
        """
        LogBuilderRegistry.register_builder(self)
        if self.options.output.log_to_stdout:
            self.add_txt("")
        from scistag.vislog.extensions.cell_sugar import LOG_CELL_METHOD_FLAG

        init_module = self.target_log.initial_module

        cell_methods = []

        if init_module is not None:
            for key, attr in self.target_log.initial_module.__dict__.items():
                if isinstance(attr, types.FunctionType):
                    is_main = False
                    if key == "vl_main":
                        from inspect import signature

                        sig = signature(attr)
                        if "vl" in sig.parameters and len(sig.parameters) == 1:
                            is_main = True

                    if LOG_CELL_METHOD_FLAG in attr.__dict__ or is_main:
                        cell_methods.append(attr)

        for key, value in self.__class__.__dict__.items():
            attr = getattr(self, key)
            if isinstance(attr, types.MethodType):
                if LOG_CELL_METHOD_FLAG in attr.__dict__:
                    cell_methods.append(attr)

        for cur_method in cell_methods:
            cell_config = cur_method.__dict__.get("__log_cell", {})
            _ = self.cell.add(
                on_build=cur_method, **cell_config, _builder_method=cur_method
            )
        LogBuilderRegistry.remove_builder(self)

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

    def add(
        self, content: LogableContent, br: bool = False, mimetype: str | None = None
    ) -> LogBuilder:
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
        :param mimetype: Defines the explicit mime type and applies it
            were possible such as parsing text provided as text/markdown or text/html.
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
            ft = filetype.guess(content)
            if ft is None:
                raise ValueError(f"Data type could not be detected")
            from scistag.imagestag.image import SUPPORTED_IMAGE_FILETYPES

            if ft.extension in SUPPORTED_IMAGE_FILETYPES:
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
            content = str(content)
        # dict or list
        if isinstance(content, (list, dict)):
            self.collection.add(content)
            return self
        if mimetype is not None:
            if mimetype == MIMETYPE_HTML or mimetype == HTML:
                self.html(str(content), linebreak=br)
                return self
            if mimetype == MIMETYPE_MARKDOWN or mimetype == MD:
                self.md(str(content))
                return self
        self.text(str(content), br=br)

    def title(self, text: str = "") -> Union[LogBuilder, ElementContext]:
        """
        Adds a title to the log

        :param text: The title's text
        :return: The builder if a text was passed, otherwise a context to insert
            custom text and elements into the heading.
        """
        return self.sub(text, level=1)

    def sub(self, text: str = "", level: int = 2) -> Union[LogBuilder, ElementContext]:
        """
        Adds a sub title to the log

        :param text: The text to add to the log
        :param level: The title level (0..5)
        :return: The builder
        """
        if text == "":
            from .common.element_context import ElementContext

            return ElementContext(
                self,
                closing_code=f"</h{level}>",
                opening_code=f"<h{level}>",
                html_only=True,
            )

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

    def text(self, text: str, br: bool = True) -> LogBuilder:
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

    def link(self, content: Any, link: str) -> LogBuilder:
        """
        Adds a hyperlink to the log

        :param content: The text or content to add to the log
        :param link: The link target
        :return: The builder
        """

        self.add_html(f'<a href="{link}">')
        self.add(content)
        self.add_html("</a>")
        return self

    def br(self, repetition=1) -> LogBuilder:
        """
        Inserts a simple line break

        :param repetition: The count of linebreaks
        :return: The builder
        """
        self.add_html("<br>" * repetition)
        self.add_txt(" ", targets="*")
        return self

    def page_break(self) -> LogBuilder:
        """
        Inserts a page break

        :return: The builder
        """
        self.add_html('<div style="break-after:page"></div>')
        self.add_txt(f"\n{'_' * 40}\n", targets="*")
        return self

    def sub_test(self, text: str) -> LogBuilder:
        """
        Adds a subtest section to the log

        :param text: The text to add to the log
        :return: The builder
        """
        self.sub(text, level=4)
        return self

    def hr(self) -> LogBuilder:
        """
        Adds a horizontal rule to the document

        :return: The builder
        """
        self.add_html("<hr>")
        self.add_txt("---", targets="*")
        return self

    def html(self, code: str | HTMLCode, linebreak: bool = True) -> LogBuilder:
        """
        Adds a html section. (only to targets supporting html)

        :param code: The html code to parse
        :param linebreak: Defines if a line break shall be inserted after the code
        """
        if isinstance(code, HTMLCode):
            code = code.to_html()
        self.add_md(code, no_break=not linebreak)
        self.add_html(code + ("\n" if linebreak else ""))
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
    def test(self) -> "TestHelper":
        """
        Provides methods to build regression tests
        """
        from .extensions.test_helper import TestHelper

        if self._test is None:
            self._test = TestHelper(self)
        return self._test

    @property
    def image(self) -> "ImageLogger":
        """
        Extension for adding images in various ways to the log
        """
        from .extensions.image_logger import ImageLogger

        if self._image is None:
            self._image = ImageLogger(self)
        return self._image

    @property
    def table(self) -> "TableLogger":
        """
        Extensions for adding tables to the log.
        """
        from .extensions.table_logger import TableLogger

        if self._table is None:
            self._table = TableLogger(self)
        return self._table

    @property
    def time(self) -> "TimeLogger":
        """
        Helper class for time measuring and logging times to the log
        """
        from .extensions.time_logger import TimeLogger

        if self._time is None:
            self._time = TimeLogger(self)
        return self._time

    @property
    def emoji(self):
        """
        Provides methods to insert Emojis into the log
        """
        from .extensions.emoji_logger import EmojiLogger

        if self._emoji is None:
            self._emoji = EmojiLogger(self)
        return self._emoji

    @property
    def log(self) -> "BasicLogger":
        """
        Provides methods for classical logging where you can flag each entry with
        an individual priority to highlight important and or filter unimportant
        entries.
        """
        from .extensions.basic_logger import BasicLogger

        if self._log is None:
            self._log = BasicLogger(self)
        return self._log

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

    @property
    def style(self) -> "StyleContext":
        """
        Extension to temporarily modify the style of the current log region or cell
        and to insert custom CSS code into the document.
        """
        from .extensions.style_context import StyleContext

        if self._style is None:
            self._style = StyleContext(self)
        return self._style

    @property
    def builder(self) -> "BuildLogger":
        """
        Extension for embedding other logs (such as LogBuilders) into the main log
        to be able to build more complex, cleanly separated solutions and to enhance the
        performance by parallelling their execution.
        """
        from .extensions.build_logger import BuildLogger

        if self._build is None:
            self._build = BuildLogger(self)
        return self._build

    @property
    def service(self) -> "LogServiceExtension":
        """
        Extension which allows the publishing of files and individual web services
        """
        return self._service

    @classmethod
    def current(cls) -> Union["LogBuilder", None]:
        """
        Returns the currently active log builder which is either handling an event
        or rebuilding the log.
        """
        return LogBuilderRegistry.current_builder()

    def code(self, code: str) -> LogBuilder:
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

    def create_backup(self) -> LogBackup:
        """
        Creates a backup of the log's content so it can for example be
        returned from a helper process or node to the main process and
        be inserted in the main log.

        See :meth:`LogBuilder.insert_backup`

        Note:
        At the moment only the HTML data can be backuped and inserted.

        :return: The backup data
        """
        self.flush()
        if HTML not in self.page_session.log_formats:
            raise ValueError("At the moment only HTML backup is supported")
        return LogBackup(data=self.page_session.get_body(HTML))

    def insert_backup(self, backup: LogBackup):
        """
        Inserts another log's backup in this log

        :param backup: The backup data
        """
        self.add_html(backup.data)

    def publish(self, path: str, content: bytes | str, **kwargs) -> "PublishingInfo":
        """
        Publishes a result data file.

        If the log is stored to disk the result data will be stored in the log's
        directory. If sub paths are used missing paths will automatically be created.

        If the log is not stored to disk the file is available at the URLs provided
        in the returned result.

        :param path: The relative path at which the data or service shall be provided
        :param content: The file's content (if provided as bytes string) or the file's
            path.
        """
        return self.service.publish(path, content, **kwargs)

    def add_html(self, html_code: str | bytes):
        """
        Adds html code directly of the HTML section of this log.

        Do not use this for logging to multiple output formats. For that
        case use :meth:`html`.

        :param html_code: The html code
        :return: True if txt logging is enabled
        """
        if self.md.html_only:
            self.page_session.write_md(html_code, no_break=True)
        self.page_session.write_html(html_code)

    def add_md(self, md_code: str, no_break: bool = False):
        """
        Adds markdown code directly of the markdown section of this log.

        Do not use this for logging to multiple output formats. For that
        case use :meth:`md`.

        :param md_code: The markdown code
        :param no_break: If defined no line break will be added
        :return: True if txt logging is enabled
        """
        if self.md.html_only:
            return
        self.page_session.write_md(md_code, no_break=no_break)

    def add_txt(
        self, txt_code: str, targets: str | set[str] | None = None, align: bool = True
    ):
        """
        Adds html code directly of the text and console section of this log.

        Do not use this for logging to multiple output formats. For that
        case use :meth:`txt`.

        :param txt_code: The text to add
        :param targets: Defines the output targets. Either "*" for all text-like
            targets or a set containing any of the targets "txt", "md" or "console".

            Pass -md to just avoid Markdown output.

            By default txt and consoles.
        :param align: Defines if alignments shall be applied to the text
        :return: True if txt logging is enabled
        """
        from scistag.vislog import TXT, CONSOLE

        if align and (
            self._cur_alignment != "left" or self._cur_alignment_block != "left"
        ):
            lines = txt_code.split("\n")
            alignment, cw = self.get_ascii_alignment()
            for index, cur_line in enumerate(lines):
                if len(cur_line) < cw:
                    missing = cw - len(cur_line)
                    if alignment == "center":
                        missing //= 2
                    lines[index] = " " * missing + cur_line
            txt_code = "\n".join(lines)
            # if len(txt_code)<cw:

        if targets is None:
            targets = {TXT, CONSOLE}
        return self.page_session.write_txt(txt_code, targets=targets)

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

    def flush(self) -> LogBuilder:
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

    def _provide_live_view(self):
        """
        Assembles a website file which automatically updates the
        logged html file as often as possible when ever it is updated
        on disk.
        """
        base_path = os.path.dirname(__file__)
        import jinja2

        environment = jinja2.Environment()
        custom_code = self.service.get_embedding_code()
        properties = {
            "VL_CUSTOM_CODE": custom_code,
            "title": self._title,
            "reload_timeout": 2000,
            "retry_frequency": 100,
            "reload_frequency": 100,
            "reload_url": "events",
            "vl_log_updates": self.options.debug.html_client.log_updates,
            "scistag_version": scistag.__version__,
        }
        template = environment.from_string(
            FileStag.load_text(base_path + "/templates/liveLog/default_liveView.html")
        )
        header_template = environment.from_string(
            FileStag.load_text(base_path + "/templates/liveLog/live_header.html")
        )
        footer_template = environment.from_string(
            FileStag.load_text(base_path + "/templates/liveLog/live_footer.html")
        )
        rendered_header = header_template.render(**properties)
        rendered_lv = template.render(**properties)
        rendered_footer = footer_template.render(**properties)
        rendered_lv = rendered_header + rendered_lv + rendered_footer
        self.service.publish("liveView.html", rendered_lv.encode("utf-8"))

    def begin_update(self) -> "PageUpdateContext":
        """
        Can be called at the beginning of a larger update block, e.g. if a page
        is completely cleared and re-built to prevent page flickering.

        Will automatically created a backup of the page's previous state and will
        return this update until end_update is called as often as begin_update.

        A PageUpdateContext can be used via `with self.begin_update()` to automatically
        call end_update once the content block is left.
        """
        return self.page_session.begin_update()

    def end_update(self):
        """
        Ends the update mode
        """
        self.page_session.end_update()

    def terminate(self):
        """
        Sets the termination state to true to request all remaining processes to
        cancel their execution.

        Note that in order to terminate the whole application or server you need
        to call the log's termination function in case of multi-session applications.
        """
        self.log.target_log.terminate()

    @property
    def terminated(self):
        """
        Defines if the current log session shall be terminated and all remaining
        tasks shall be cancelled.
        """
        return self.target_log.terminated

    def get_result(self) -> Any:
        """
        Returns the builder's results. That is usually the whole page, but in case
        of usage as singleton and/or web service may also return other kinds of
        data.

        :return: The result data
        """
        result_data = {}
        if self.nested:
            for cur_format in self.options.output.formats_out:
                index_name = self.page_session.get_index_name(cur_format)
                if index_name is None:
                    continue
                result_data = {index_name: self.page_session.get_body(cur_format)}
        else:
            for cur_format in self.options.output.formats_out:
                index_name = self.page_session.get_index_name(cur_format)
                if index_name is None:
                    continue
                result_data = {index_name: self.page_session.get_page(cur_format)}
        return result_data

    def __enter__(self):
        LogBuilderRegistry.register_builder(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        LogBuilderRegistry.remove_builder(self)

    def get_ascii_alignment(self) -> (str, int | None):
        """
        Returns the desired, horizontal alignment for ascii text

        :return: The alignment, either "left", "center" or "right", the minimum width,
            if the alignment is not "left", otherwise None
        """
        align = self._cur_alignment
        if self._cur_alignment_block != "left":
            align = self._cur_alignment_block
        if align != "left":
            return align, self._console_size[0]
        else:
            return "left", None
