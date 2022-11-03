"""
Helper functions to export images of rendering methods for manual verification
"""
from __future__ import annotations

import base64
import hashlib
import html
import inspect
import io
import json
import os
import shutil
import time
from collections import Counter
from typing import Any, Optional, TYPE_CHECKING, Callable, Union

import filetype
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import scistag.logstag.visual_log.widgets.log_button
from scistag.common import StagLock, Component, Cache
from scistag.filestag import FileStag, FilePath
from scistag.imagestag import Image, Canvas, Size2D, Size2DTypes, \
    InterpolationMethod
from scistag.plotstag import Figure, Plot, MPHelper
from scistag.webstag import web_fetch
from scistag.logstag import LogLevel
from scistag.logstag.console_stag import Console
from scistag.logstag.visual_log.sub_log import SubLog, SubLogLock
from scistag.logstag.visual_log.visual_log_service import VisualLogService
from ...webstag.web_helper import WebHelper

# Error messages

_ONLY_AUTO_CLEAR_ON_CONTINUOUS = "'auto_clear' can only be used in " \
                                 "combination with 'continuous=True'"

_CONTINUOUS_NO_EFFECT_WITHOUT_BUILDER = \
    "continuous has no effect and should not be " \
    "passed if builder is None"

_CONTINUOUS_REQUIRES_OVERWRITE = "It does not make sense to run the " \
                                 "log with continuous=True to update " \
                                 "the log frequently if you forbid " \
                                 "updating it."

_CONTINUOUS_REQUIRED_BG_THREAD = "To update the log via this method " \
                                 "you have to set 'mt' to True " \
                                 "so the server can run in a " \
                                 "background thread."

LOG_EVENT_CACHE_NAME = "__logEvents"
"Name of the cache entry in which the log events are stored"

if TYPE_CHECKING:
    from scistag.webstag.server import WebStagServer
    from scistag.webstag.server import WebStagService
    from scistag.logstag.visual_log.pyplot_log_context import \
        PyPlotLogContext
    from .visual_log_renderer import VisualLogRenderer
    from .visual_log_renderer_html import VisualLogHtmlRenderer
    from .widgets.log_widget import LogWidget
    from .widgets.log_button import LogButton

HTML = "html"
"Html output"
CONSOLE = "console"
"Console output"
TXT = "txt"
"Txt output"
MD = "md"
"Markdown output"

MAIN_LOG = "mainLog"
"The name of the main log"

if TYPE_CHECKING:
    from scistag.imagestag.pixel_format import PixelFormat
    from scistag.logstag.visual_log.log_event import LogEvent

BuilderCallback = Callable[["VisualLog"], None]
"""
Type definition for a function which can be passed to VisualLog's initializer
to be called once or continuously to update the log.
"""

BuilderTypes = Union[BuilderCallback]
"""
The supported builder callback types
"""


class VisualLog:
    """
    The VisualLog class enables you to create detailed, static data processing
    documentation logs in various formats such as html, md and pdf up to
    complex interactive browser based HTML and JavaScript applications
    forwarding all user inputs via JavaScript to your Python logic and the
    updates you trigger back to the user's view in the browser.

    To view the log live in your IDE next to your code:
    - Build the log via run_server.
    - For a detailed example see the camera-demo at
        https://github.com/SciStag/SciStag/tree/main/scistag/examples/logstag
    - PyCharm: Ctrl-Shift-A -> Open Source Code From URL -> Paste the live
        url -> Click on the small PyCharm icon in the upper right corner
    - VS Code: Not supported yet. Open the /live URL above in a browser and
        align your IDE and browser windows side by side, e.g. with Win
        Key+Left and Win Key+Right
    """

    def __init__(self, target_dir: str = "./logs",
                 title: str = "SciStag - VisualLog",
                 formats_out: set[str] | None = None,
                 ref_dir: str | None = None,
                 tmp_dir: str | None = None,
                 clear_target_dir: bool = False,
                 log_to_disk=True,
                 embed_images: bool | None = None,
                 continuous_write=False,
                 refresh_time_s=0.5,
                 max_fig_size: Size2DTypes | None = None,
                 image_format: str | tuple[str, int] = "png",
                 image_quality: int = 90,
                 cache_dir: str | None = None,
                 cache_version: int = 1,
                 cache_name: str = "",
                 auto_reload: bool | BuilderTypes = False):
        """
        :param target_dir: The output directory
        :param title: The log's name
        :param formats_out: A set of the formats to export.

            "html", "txt" (pure Text)  and "md" (markdown) are supported.

            By default only html files will be created.
        :param ref_dir: The directory in which the reference data objects
            can be stored.
        :param tmp_dir: A directory in which temporary files can be stored.
            Will be deleted upon finalization.
        :param clear_target_dir: Defines if the target dir shall be deleted
            before starting (take care!)
        :param log_to_disk: Defines if the logger shall write it's results
            to disk. True by default.
        :param embed_images: Defines if images shall be directly embedded into
            the HTML log instead of being stored as separate files.

            By default True if Markdown is not set as one of the "formats_out",
            otherwise False by default as Markdown will need the files on disk.
        :param continuous_write: Defines if the log shall be written to disk
            after every added element. False by default.
        :param refresh_time_s: The time interval in seconds in which the
            auto-reloader html page (liveView.html) tries to refresh the page.
            The lower the time the more often the page is refreshed.
        :param max_fig_size: The optimum, maximum width and height for
            embedded figures and images
        :param image_format: The default output image format to store images
            and figures with. "png" by default.

            You can also pass the image format and image quality in a tuple
            such as ("jpg", 60).

            Alternatively "jpg" or "bmp" can be used (to minimize the bandwidth
            or in the later case if you are the intranet w/ unlimited bandwidth
            and want to host it live at maximum performance).
        :param image_quality: The default image output quality. 90 by default.

            Values between 0 and 100 are valid.
        :param cache_version: The cache version. 1 by default.

            When ever you change this version all old cache values will be
            removed and/or ignored from the cache.
        :param cache_dir: The directory in which data which shall be cached
            between multiple execution sessions shall be dumped to disk.

            By default "{target_dir}/.stscache".
        :param cache_name: The cache's identifier. If multiple logs store data
            into the same logging directory this can be used to ensure their
            caching directories don't accidentally overlap w/o having to
            provide the whole path via cache_dir.
        :param auto_reload: Defines if this log will be executed in auto_reload
            mode in its cache should be update and restored each turn.
        """
        try:
            if clear_target_dir and log_to_disk:
                if clear_target_dir and log_to_disk:
                    shutil.rmtree(target_dir)
        except FileNotFoundError:
            pass
        if formats_out is None:
            formats_out = {"html"}

        self._cache: Cache | None = None
        """
        The log's data cache to store computation results between execution
        sessions
        """

        self._title = title
        "The log's title"
        self.target_dir = os.path.abspath(target_dir)
        "The directory in which the logs shall be stored"
        # setup the cache
        do_auto_reload = isinstance(auto_reload, bool) and auto_reload \
                         or auto_reload is not None
        self._setup_cache(do_auto_reload, cache_version, cache_dir, cache_name)
        self.ref_dir = FilePath.norm_path(
            self.target_dir + "/ref" if ref_dir is None else ref_dir)
        "The directory in which reference files for comparison shall be stored"
        self._tmp_path = FilePath.norm_path(
            self.target_dir + "/temp" if tmp_dir is None else tmp_dir)
        "Output directory for temporary files"
        if log_to_disk:
            os.makedirs(self.target_dir, exist_ok=True)
        self._log_to_disk = log_to_disk
        "Defines if the images and the html data shall be written to disk"
        self._log_images = True
        "Defines if images shall be logged to disk"
        self.name_counter = Counter()
        "Counter for file names to prevent writing to the same file twice"
        self.title_counter = Counter()
        "Counter for titles to numerate the if appearing twice"
        self._refresh_time_s = refresh_time_s
        """
        The time interval with which the log shall be refreshed when using
        the liveViewer (see Live_view)
        """
        if max_fig_size is not None and not isinstance(max_fig_size, Size2D):
            max_fig_size = Size2D(max_fig_size)
        else:
            max_fig_size = Size2D(1024, 1024)
        "Defines the preview's width and height"
        self._log_formats = formats_out
        "Defines if text shall be logged"
        self._log_formats.add(CONSOLE)
        self._log_stag: list[SubLog] = []
        """
        A stag for temporary switching log targets and to created 'nested"
        logs.
        """
        self.sub_log_data: dict[str, dict[str, bytes]] = {}
        """
        Contains the content of each "sub log", see :meth:`begin_sub_log`.
        """
        self._logs: dict[str, list[bytes]] = {element: [] for element in
                                              sorted(self._log_formats)}
        """
        Contains the log data for each output type
        """
        self._log_stag.append(SubLog(logs=self._logs, target="",
                                     max_fig_size=max_fig_size.to_int_tuple()))
        self.continuous_write = continuous_write
        "If defined the output logs will be updated after every log"
        self.markdown_html = True
        "Defines if markdown shall support html embedding"
        self._log_txt_images = True
        "Defines if images shall also be logged to text files as ASCII"
        self._use_tabulate = True
        "Defines if tabulate may be used"
        self._use_pretty_html_table = True
        "Defines if pretty html shall be used"
        self._html_table_style = 'blue_light'
        "The pretty html style to be used"
        self._txt_table_format = "rounded_outline"
        "The text table format to use in tabulate"
        self._md_table_format = "github"
        "The markdown table format to use"
        self._embed_images = embed_images if embed_images is not None else \
            not MD in formats_out
        "If defined images will be embedded directly into the HTML code"
        self._image_format = image_format
        "The default image type to use for storage"
        self._image_quality = image_quality
        "The image compression quality"
        self._html_export = HTML in self._log_formats
        "Defines if HTML gets exported"
        self._md_export = MD in self._log_formats
        "Defines if markdown gets exported"
        self._txt_export = TXT in self._log_formats
        "Defines if txt gets exported"
        self._txt_filename = self.target_dir + "/index.txt"
        "The name of the txt file to which we shall save"
        self._html_filename = self.target_dir + "/index.html"
        "The name of the html file to which we shall save"
        self._md_filename = self.target_dir + "/index.md"
        "The name of the markdown file to which we shall save"
        self._consoles: list[Console] = []
        "Attached consoles to which the data shall be logged"
        self._log_limit = -1
        """
        The current log limit (maximum number of rows before starting deleting
        the oldest ones)
        """
        from .visual_log_renderer_html import VisualLogHtmlRenderer
        self._renderers: dict[str, "VisualLogRenderer"] = {
            HTML: VisualLogHtmlRenderer(title=self._title)}
        "The renderers for the single supported formats"
        self.forward_targets: dict[str, VisualLog] = {}
        "List of logs to which all rendering commands shall be forwarded"
        self._page_lock = StagLock()
        "Lock for multithread secure access to the latest page update"
        self._page_backups: dict[str, bytes] = {}
        """
        A backup of the latest rendered page of each dynamic data type
        (excluding PDFs and PNGs which are just created on demand)
        """
        self._body_backups: dict[str, bytes] = {}
        """
        A backup of the latest body renderings for each content type
        """
        self.static_files: dict[str, bytes] = {}
        "Statically hosted files for a pure web based provision of the log"
        self._shall_terminate = False
        """
        Defines if the log service shall be terminated, e.g if it's running
        endlessly via :meth:`run` or :meth:`run_server`.
        """
        self._provide_live_view()  # setup live view html page
        self._server: Union["WebStagServer", None] = None
        "The web server (if one was being started via :meth:`run_server`)"
        # Statistics
        self._start_time = time.time()
        "The time stamp of when the log was creation"
        self._total_update_counter = 0
        "The total number of updates to this log"
        self._update_counter = 0
        # The amount of updates since the last statistics update
        self._last_statistic_update = time.time()
        "THe last time the _update rate was computed as time stamp"
        self._update_rate: float = 0
        # The last computed updated rate in updates per second
        self._events = []
        "List of unhandled events"
        self._widgets = {}
        "Set of widgets"
        if do_auto_reload:
            self._events = self.cache.get(LOG_EVENT_CACHE_NAME, default=[])
        self._invalid = False
        "Defines if this log was invalidated via :meth:`invalidate`"
        # execute auto-reloader if provided
        if not isinstance(auto_reload, bool) and auto_reload is not None:
            self.run_server(host_name="127.0.0.1",
                            builder=auto_reload, auto_reload=True,
                            auto_reload_stag_level=2)

    @property
    def refresh_time_s(self) -> float:
        """
        The (maximum) refresh time of the log in seconds as passed in
        the constructor.

        If the log is updated via `run_server` or `run` via `continuous=True`
        this is the frequency it should get updated with.
        """
        return self._refresh_time_s

    def load_old_logs(self) -> bool:
        """
        Tries to load the old logs from disk so they can be hosted via
            :meth:`run_server`.

        :return: True if the logs could be loaded
        """
        raise NotImplementedError("Not implemented yet")  # TODO Implement

    def terminate(self):
        """
        Sets the termination state to true so that if the log was
        initialized with the flag `continuous=True` it can be terminated
        from within the logging function.
        """
        with self._page_lock:
            self._shall_terminate = True

    def add_static_file(self, filename: str, content: bytes):
        """
        Provides a file statically, e.g. to provide it via a
            VisualLiveLogServer.

        Multi-thread safe function.

        :param filename: The name of the data to add
        :param content: The file's content
        """
        with self._page_lock:
            self.static_files[filename] = content

    def get_file(self, filename: str) -> bytes | None:
        """
        Tries to receive a file created by this log, either stored locally
        or in memory via :meth:`add_static_file`.

        :param filename: The file's name
        :return: The file's content (if available)
        """
        with self._page_lock:
            if filename in self.static_files:
                return self.static_files[filename]
            abs_filename = os.path.abspath(self.target_dir + "/" + filename)
            if not abs_filename.startswith(self.target_dir):
                return None
            return FileStag.load(abs_filename)

    def set_log_limit(self, limit: int):
        """
        Changes the maximum count of log rows for the current sub log.

        If the number gets exceeded it will automatically start deleting the
        oldest logs.

        :param limit: The new limit. -1 = None
        """
        self._log_stag[-1].log_limit = limit
        self._log_limit = limit

    def add_console(self, console: Console):
        """
        Adds an advanced console as target to the log

        :param console: The console to add
        """
        self._consoles.append(console)

    @staticmethod
    def _get_module_path() -> str:
        """
        Returns the path of the VisualStag module

        :return: The path
        """
        return FilePath.dirname(__file__)

    def clear_logs(self):
        """
        Clears the whole log (excluding headers and footers)
        """
        for key in self._logs.keys():
            self._logs[key].clear()

    def embed(self, log: VisualLog):
        """
        Embeds another VisualLog's content into this one

        :param log: The source log
        """
        for cur_format in self._log_formats:
            if cur_format in log._log_formats:
                self._logs[cur_format].append(log.get_body(cur_format))

    @property
    def max_fig_size(self) -> Size2D:
        """
        The maximum figure size in pixels
        """
        return Size2D(self._log_stag[-1].max_fig_size)

    def clip_logs(self):
        """
        Checks if the log limited exceeded and clips old logs if necessary.
        """
        if self._log_limit != -1:
            for key, elements in self._logs.items():
                exc_elements = len(elements) - self._log_limit
                if exc_elements > 0:
                    self._logs[key] = elements[exc_elements:]

    def begin_sub_log(self, target: str,
                      max_fig_size: Size2DTypes | None = None) -> SubLogLock:
        """
        Pushes the current log target to create a sub log.

        You can call this method for the same target multiple
        times so the logs get attached to each other.
        When ever :meth:`end_sub_log` is called self.sub_log_data is updated
        with all elements on the stack which participate towards the
        same target. These can then (for example) be used to combine them
        to a custom html or txt log via customizing the `get_body` function.

        Usage:

        ..  code-block: Python

            with v.begin_sub_log():
                ...

        :param target: The sub log's name in which the content shall be stored.
            See :attr:`sub_log_data`.
        :param max_fig_size: Defines the maximum size of visual elements
        """
        if len(self._log_stag) > 100:
            raise AssertionError("Maximum log stag depth exceeded, something "
                                 "is likely wrong and you did not cleanly "
                                 "leave the current update's section.")
        new_logs = {}
        for key, value in self._logs.items():
            new_logs[key] = []

        if max_fig_size is not None:
            if not isinstance(max_fig_size, Size2D):
                max_fig_size = Size2D(max_fig_size)
        else:
            max_fig_size = self._log_stag[0].max_fig_size

        self._log_stag.append(SubLog(logs=new_logs, target=target,
                                     max_fig_size=max_fig_size.to_int_tuple()))
        self._logs = new_logs
        return SubLogLock(self)

    def end_sub_log(self):
        """
        Ends a sub log, aggregates all logs which participated to the
        current target and stores the content in sub_log_data[target] which
        can then be used to customize def get_body()
        """
        if len(self._log_stag) == 0:
            raise AssertionError("Tried to decrease log stag without remaining "
                                 "elements")
        top_target = self._log_stag[-1].target
        target_data = {}
        # initialize empty data streams for each target type (md, html etc.)
        for key, value in self._logs.items():
            target_data[key] = b""
        for element in self._log_stag:  # for all logs on the stag
            if element.target == top_target:  # if it matches our target type
                cur_logs = element.logs
                # for all target types of this log
                for target_type, target_log_list in cur_logs.items():
                    new_data = b"".join(target_log_list)
                    if len(new_data) >= 1:
                        pass
                    target_data[target_type] += new_data
        self.sub_log_data[top_target] = target_data
        self._log_stag.pop()
        self._logs = self._log_stag[-1].logs  # restore previous log target
        self._log_limit = self._log_stag[-1].log_limit  # restore log limi

    def _need_images_on_disk(self) -> bool:
        """
        Returns if images NEED to be stored on disk

        :return: True if they do
        """
        return self._md_export or not self._embed_images

    def _provide_live_view(self):
        """
        Assembles a website file which automatically updates the
        logged html file as often as possible when ever it is updated
        on disk.
        """
        base_path = self._get_module_path()
        css = FileStag.load(base_path + "/css/visual_log.css")
        if self._log_to_disk:
            FileStag.save(f"{self.target_dir}/css/visual_log.css",
                          css,
                          create_dir=True)
        self.add_static_file("css/visual_log.css",
                             css)
        import jinja2
        environment = jinja2.Environment()
        template = environment.from_string(
            FileStag.load_text(base_path + "/templates/liveView.html"))
        rendered_lv = template.render(title=self._title,
                                      reload_timeout=2000,
                                      retry_frequency=100,
                                      reload_frequency=int(
                                          self._refresh_time_s * 1000),
                                      reload_url="index.html")
        if self._log_to_disk:
            FileStag.save_text(self.target_dir + "/liveView.html",
                               rendered_lv)
        rendered_lv = template.render(title=self._title,
                                      reload_timeout=2000,
                                      retry_frequency=100,
                                      reload_frequency=int(
                                          self._refresh_time_s * 1000),
                                      reload_url="index")
        self.add_static_file('liveView.html',
                             rendered_lv)

    def table(self, table_data: list[list[any]], index=False, header=False):
        """
        Adds a table to the log.

        :param table_data: The table data. A list of rows including a list of
            columns.

            Each row has to provide the same count of columns.

            At the moment only string content is supported.
        :param index: Defines if the table has an index column
        :param header: Defines if the table has a header
        """
        code = '<table class="log_table">\n'
        for row_index, row in enumerate(table_data):
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
        self.html(code)

    def image(self, source: Image | Canvas | str | bytes | np.ndarray,
              name: str | None = None,
              alt_text: str | None = None,
              pixel_format: Optional["PixelFormat"] | str | None = None,
              download: bool = False,
              scaling: float = 1.0,
              max_width: int | float | None = None,
              optical_scaling: float = 1.0,
              html_linebreak=True):
        """
        Writes the image to disk for manual verification

        :param name: The name of the image under which it shall be stored
            on disk (in case write_to_disk is enabled).
        :param source: The data object, e.g. an scitag.imagestag.Image, a numpy array, an URL or a FileStag
            compatible link.
        :param alt_text: An alternative text if no image can be displayed
        :param pixel_format: The pixel format (in case the image is passed
            as numpy array). By default gray will be used for single channel,
            RGB for triple band and RGBA for quad band sources.
        :param download: Defines if an image shall be downloaded
        :param scaling: The factor by which the image shall be scaled
        :param max_width: Defines if the image shall be scaled to a given size.

            Possible values
            - True = Scale to the log's max_fig_size.
            - float = Scale the image to the defined percentual size of the max_fig_size, 1.0 = max_fig_size

        :param optical_scaling: Defines the factor with which the image shall
            be visualized on the html page without really rescaling the image
            itself and thus giving the possibility to zoom in the browser.
        :param html_linebreak: Defines if a linebreak shall be inserted after
            the image.
        """
        if not self._log_images:
            return
        if name is None:
            name = "image"
        if alt_text is None:
            alt_text = name
        if self._log_txt_images or max_width is not None or scaling != 1.0:
            download = True
        if isinstance(source, np.ndarray):
            source = Image(source, pixel_format=pixel_format)
        html_lb = "<br>" if html_linebreak else ""
        if isinstance(source, str):
            if not source.lower().startswith("http") or download or \
                    self._embed_images:
                source = Image(source=source)
            else:
                self._insert_image_reference(name, source, alt_text, scaling,
                                             html_linebreak)
                return
        self.name_counter[name] += 1
        filename = name
        if self.name_counter[name] > 1:
            filename += f"__{self.name_counter[name]}"
        if isinstance(source, Canvas):
            source = source.to_image()
        file_location = ""
        size_definition = ""
        if scaling != 1.0 or optical_scaling != 1.0 or max_width is not None:
            max_size = None
            if max_width is not None:
                if scaling != 1.0:
                    raise ValueError("Can't set max_size and scaling at the same time.")
                scaling = None
                if isinstance(max_width, float):
                    max_width = int(round(self.max_fig_size.width * max_width))
                max_size = (max_width, None)
            if not isinstance(source, Image):
                source = Image(source)
            source = source.resized_ext(factor=scaling, max_size=max_size)
            size_definition = \
                f" width={int(round(source.width * optical_scaling))} " \
                f"height={int(round(source.height * optical_scaling))}"
        # encode image if required
        if isinstance(source, bytes):
            encoded_image = source
        else:
            encoded_image = source.encode(
                filetype=self._image_format,
                quality=self._image_quality)
        # store on disk if required
        if self._log_to_disk:
            file_location = self._log_image_to_disk(filename, name, source,
                                                    encoded_image,
                                                    html_linebreak)
        # embed if required
        if self._embed_images:
            embed_data = self._build_get_embedded_image(encoded_image)
            file_location = embed_data
        if len(file_location):
            self._add_html(
                f'<img src="{file_location}" {size_definition}>{html_lb}\n')
        if self._log_txt_images and (self._txt_export or len(self._consoles)):
            if not isinstance(source, Image):
                source = Image(source)
            max_width = min(max(source.width / 1024 * 80, 1), 80)
            self._add_txt(source.to_ascii(max_width=max_width))
            self._add_txt(f"Image: {alt_text}\n")
        else:
            self._add_txt(f"\n[IMAGE][{alt_text}]\n")
        self.clip_logs()

    def _insert_image_reference(self,
                                name,
                                source,
                                alt_text,
                                scaling: float = 1.0,
                                html_scaling: float = 1.0,
                                html_linebreak: bool = True):
        """
        Inserts a link to an image in the html logger without actually
        downloading or storing the image locally

        :param name: The image's name
        :param source: The url
        :param alt_text: The alternative display text
        :param scaling: The scaling factor
        :param html_scaling: Defines the factor with which the image shall
            be visualized on the html page without really rescaling the image
            itself and thus giving the possibility to zoom in the browser.
        :param html_linebreak: Defines if a linebreak shall be inserted
            after the image
        """
        html_lb = "<br>" if html_linebreak else ""
        if scaling != 1.0 or html_scaling != 1.0:
            image = Image(source)
            width, height = (int(round(image.width * scaling * html_scaling)),
                             int(round(image.height * scaling * html_scaling)))
            self._add_html(
                f'<img src="{source}" with={width} height={height}>{html_lb}')
        else:
            self._add_html(f'<img src="{source}">{html_lb}')
        self._add_md(f'![{name}]({source})\n')
        self._add_txt(f"\n[IMAGE][{alt_text}]\n")

    def _log_image_to_disk(self,
                           filename,
                           name,
                           source,
                           encoded_image,
                           html_linebreak) -> str:
        """
        Stores an image on the disk

        :param filename:  The output filename
        :param name:  The image's name
        :param source: The data source
        :param encoded_image: The encoded image
        :param html_linebreak: Defines if a linebreak shall be inserted
            after the image
        :return: The file location of the store image
        """
        html_lb = "<br>" if html_linebreak else ""
        file_location = ""
        if isinstance(source, bytes):
            import filetype
            file_type = filetype.guess(source)
            target_filename = self.target_dir + \
                              f"/{filename}.{file_type.extension}"
            if self._need_images_on_disk():
                FileStag.save(target_filename, source)
        else:
            extension = (self._image_format if
                         isinstance(self._image_format, str)
                         else self._image_format[0])
            target_filename = \
                self.target_dir + f"/{filename}.{extension}"
            if self._need_images_on_disk():
                FileStag.save(target_filename, encoded_image)
        if not self._embed_images:
            file_location = os.path.basename(target_filename)
        if self._md_export:
            self._add_md(
                f'![{name}]({os.path.basename(target_filename)})\n')
        return file_location

    @staticmethod
    def _build_get_embedded_image(source: bytes) -> str:
        """
        Encodes an image to ASCII to embed it directly into an HTML page

        :param source: The source data
        :return: The string to embed
        """
        ft = filetype.guess(source)
        mime_type = ft.mime
        base64_data = base64.encodebytes(source).decode("ASCII")
        return f"data:{mime_type};base64,{base64_data}"

    def evaluate(self, code: str, log_code: bool = True) -> Any:
        """
        Runs a piece of code and returns it's output

        :param code: The code to execute
        :param log_code: Defines if the code shall be added to the log
        :return: The returned data (if any)
        """
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
        self._add_txt("\n_________________________________________________________________________________\n", md=True)

    def sub(self, text: str, level: int = 2):
        """
        Adds a sub title to the log

        :param text: The text to add to the log
        :param level: The title level (0..5)
        :return:
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

    def test(self, text: str):
        """
        Adds a test section to the log

        :param text: The text to add to the log
        :return:
        """
        self.sub(text, level=1)

    def sub_test(self, text: str):
        """
        Adds a sub test section to the log

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

    def log(self, *args: Any, level: LogLevel | str = LogLevel.INFO,
            space: str = " "):
        """
        Adds a log text to the log

        :param text: The text to add to the log
        :param level: The importance / category of the log entry
        :param space: The character or text to be used for spaces
        :return:
        """
        if isinstance(level, str):
            level = LogLevel(level)
        elements = [str(element) for element in args]
        text = space.join(elements)
        if text is None:
            text = "None"
        if not isinstance(text, str):
            text = str(text)
        print(text)
        for element in self.forward_targets.values():
            element.log(text, level=level)
        escaped_text = self._encode_html(text)
        self._add_html(
            f'<p class="logtext">{self._html_linebreaks(escaped_text)}</p>'
            f'<br>\n')
        if MD in self._logs and len(self._logs[MD]) > 0:
            last_md_log: str = self._logs[MD][-1].decode("utf-8")
            if last_md_log.endswith("```\n"):
                self._add_md(f"{text}\n```")
        else:
            self._add_md(f"```\n{text}\n```")
        self._add_txt(text)
        self.clip_logs()

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
        self.log("".join(elements))

    def get_vl_statistics(self) -> dict:
        """
        Returns statistics about the log

        :return: A dictionary with statistics about the log such as
            - totalUpdateCount - How often was the log updated?
            - updatesPerSecond - How often was the log updated per second
            - upTime - How long is the log being updated?
        """
        return {"totalUpdateCount": self._total_update_counter,
                "updatesPerSecond": self._update_rate,
                "upTime": time.time() - self._start_time}

    def log_vl_statistics(self):
        """
        Adds statistics about the VisualLog as table to the log
        """
        self.table([["Updates", f"{self._total_update_counter} total updates"],
                    ["Effective lps",
                     f"{self._update_rate:0.2f} updates per second"],
                    ["Uptime",
                     f"{time.time() - self._start_time:0.2f} seconds"]],
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
        if self._use_pretty_html_table:
            try:
                import pretty_html_table
                html_code = pretty_html_table.build_table(df,
                                                          self._html_table_style,
                                                          index=index)
            except ModuleNotFoundError:  # pragma: no-cover
                html_code = df.to_html(index=index)
        else:
            html_code = df.to_html(index=index)
        self._add_html(html_code + "\n")
        if self._use_tabulate:
            try:
                import tabulate
                md_table = df.to_markdown(index=index,
                                          tablefmt=self._md_table_format)
                self._add_md(md_table)
                self._add_txt(
                    df.to_markdown(index=index,
                                   tablefmt=self._txt_table_format) + "\n")
                return
            except ModuleNotFoundError:  # pragma: no-cover
                pass
        else:
            string_table = df.to_string(index=index) + "\n"
            if self.markdown_html:
                self._add_md(html_code)
            else:
                self._add_md(string_table)
            self._add_txt(string_table)
        self.clip_logs()

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
        if not self._log_images and _out_image_data is None:
            return
        if isinstance(figure, (Figure, Plot)):
            image = figure.render()
            self.image(image, name, alt_text=alt_text)
            if _out_image_data is not None:
                _out_image_data.write(
                    image.encode(filetype=self._image_format,
                                 quality=self._image_quality))
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
        if len(self._consoles) or self._txt_export:
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

    def hash_check_log(self, value, assumed):
        """
        Verifies a hash and adds the outcome of a hash check to the output

        :param value: The hash value
        :param assumed: The assumed value
        """
        if value != assumed:
            self.log(
                f"⚠️Hash validation failed!\nValue:  {value}\nAssumed: {assumed}")
            self.write_to_disk()
            raise AssertionError("Hash mismatch - "
                                 f"Found: {value} - "
                                 f"Assumed: {assumed}")
        else:
            self.log(f"{assumed} ✔")

    def assert_figure(self, name: str,
                      figure: plt.Figure | plt.Axes | Figure | Plot,
                      hash_val: str,
                      alt_text: str | None = None):
        """
        Adds a figure to the log and verifies it's content to a checksum

        :param name: The figure's name
        :param figure: The figure to log
        :param alt_text: An alternative text to display if the figure can
            not be displayed.
        :param hash_val: The hash value to compare to (a checksum of all
            pixels). The correct will be logged via an assertion upon failure
            and can then be copies & pasted.
        """
        image_data = io.BytesIO()
        self.figure(figure=figure, name=name, alt_text=alt_text,
                    _out_image_data=image_data)
        assert len(image_data.getvalue()) > 0
        result_hash_val = hashlib.md5(image_data.getvalue()).hexdigest()
        self.hash_check_log(result_hash_val, hash_val)

    def assert_image(self, name: str, source: Image | Canvas, hash_val: str,
                     scaling: float = 1.0,
                     alt_text: str | None = None):
        """
        Assert an image object and verifies it's hash value matches the object's
        hash.

        :param name: The name of the object
        :param source: The data to log
        :param hash_val: The hash value to compare to (a checksum of all
            pixels). The correct will be logged via an assertion upon failure
            and can then be copies & pasted.
        :param scaling: The factor by which the image shall be scaled
        :param alt_text: An alternative text to display if the image can
            not be displayed.
        """
        result_hash_val = self.log_and_hash_image(name=name,
                                                  data=source,
                                                  scaling=scaling,
                                                  alt_text=alt_text)
        self.hash_check_log(result_hash_val, hash_val)

    def log_and_hash_image(self, name: str,
                           data: Image | Canvas,
                           alt_text: str | None = None,
                           scaling: float = 1.0) -> str:
        """
        Writes the image to disk for manual verification (if enabled in the
        test_config) and returns it's hash.

        :param name: The name of the test.
            Will result in a file named logs/TEST_DIR/test_name.png
        :param data: The image object
        :param alt_text: An alternative text to display if the image can
            not be displayed.
        :param scaling: The factor by which the image shall be scaled
        :return: The image's hash for consistency checks
        """
        if isinstance(data, Canvas):
            data = data.to_image()
        self.image(source=data, name=name, alt_text=alt_text, scaling=scaling)
        return data.get_hash()

    def assert_text(self, name: str, text: str, hash_val: str):
        """
        Asserts a text for validity and logs it

        :param name: The assertion's name
        :param text: The text data
        :param hash_val: The assumed hash value
        """
        result_hash_val = hashlib.md5(text.encode("utf-8")).hexdigest()
        self.text(text)
        self.hash_check_log(result_hash_val, hash_val)

    def assert_df(self, name: str,
                  df: pd.DataFrame,
                  dump: bool = False,
                  hash_val: str | None = None):
        """
        Asserts the integrity of a dataframe

        :param name: The name
        :param df: The data frame's part to verify
        :param dump: Defines if the data fram shall be dumped to disk.
            To this once for a new data frame to create a reference
        :param hash_val: If specified the dataframe will get dumped as csv
            of which the hash value is compared to the one passed.
        """
        if hash_val is not None:
            output = io.BytesIO()
            df.to_csv(output)
            result_hash_val = hashlib.md5(output.getvalue()).hexdigest()
            if result_hash_val != hash_val:
                self.write_to_disk()
                raise AssertionError("Hash mismatch - "
                                     f"Found: {result_hash_val} - "
                                     f"Assumed: {hash_val}")
            return
        if dump:
            output = io.BytesIO()
            df.to_parquet(output, engine='pyarrow')
            self.save_ref(name, output.getvalue())
            print(f"Warning - Updating test reference of {name}")
        comp_data = self.load_ref(name)
        if comp_data is None:
            raise AssertionError(f"No reference data provided for {name}")
        comp_df = pd.read_parquet(io.BytesIO(comp_data), engine='pyarrow')
        if not comp_df.equals(df):
            raise AssertionError(
                f"Data mismatch between {name} and it's reference")

    def assert_np(self, name: str,
                  data: np.ndarray,
                  variance_abs: float | None = None,
                  dump: bool = False,
                  rounded: int = None,
                  hash_val: bool | None = None):
        """
        Asserts a nunpy array for validity and logs it

        :param name: The assertion's name
        :param data: The data
        :param variance_abs: The maximum, absolute variance to the original,
            0.0 by default.
        :param dump: Defines if the current dump shall be overwritten.
            Set this once to true when you on purpose changed the data and
             verified it.
        :param rounded: Pass this if you want to hash floating point
            arrays where a rounded integer precision is enough.

            rounded defines how many digits behind the comma are relevant,
            so 0 rounds to full ints, +1 rounds to 0.1, +2 rounds to 0.01
            etc. pp.
        :param hash_val: The hash value to use as orientation.

            Do not use this for floating point data types due to
            platform dependent (slight) data discrepancies.
        """
        if rounded is not None:
            data = (data * (10 ** rounded)).astype(int)
        if hash_val is not None:
            if data.dtype == float:
                raise NotImplementedError("Hashing not supported for float"
                                          "matrices")
            result_hash_val = hashlib.md5(data.tobytes()).hexdigest()
            if result_hash_val != hash_val:
                self.write_to_disk()
                raise AssertionError("Hash mismatch - "
                                     f"Found: {result_hash_val} - "
                                     f"Assumed: {hash_val}")
            return
        if dump:
            output = io.BytesIO()
            np.save(output, data)
            self.save_ref(name, output.getvalue())
            print(f"Warning - Updating test reference of {name}")
        comp_data = self.load_ref(name)
        if comp_data is None:
            raise AssertionError(f"No reference data provided for {name}")
        np_array = np.load(io.BytesIO(comp_data))
        if variance_abs == 0.0 or variance_abs is None:
            if np.all(np_array == data):
                return
        else:
            if np.all(np.abs(np_array - data) <= variance_abs):
                return
        raise AssertionError(f"Data mismatch between {name} and it's reference")

    def assert_val(self, name: str,
                   data: dict | list | str | Image | Figure | pd.DataFrame,
                   hash_val: str | None = None):
        """
        Asserts a text for validity and logs it

        :param name: The assertion's name
        :param data: The data
        :param hash_val: The assumed hash value (not required for data w/
            reference)
        """
        # image
        if isinstance(data, Image):
            self.assert_image(name, data, hash_val=hash_val)
            return
        # figure
        if isinstance(data, Figure):
            self.assert_figure(name, data, hash_val=hash_val)
            return
        # pandas data frame
        if isinstance(data, pd.DataFrame):
            self.assert_df(name, data)
            return
        # numpy array
        if isinstance(data, np.ndarray):
            self.assert_np(name, data, hash_val=hash_val)
            return
        if isinstance(data, str):
            self.assert_text(name, data, hash_val=hash_val)
            return
            # dict or list
        if isinstance(data, (list, dict, str)):
            self.log(str(data))  # no beautiful logging supported yet
            data = json.dumps(data).encode("utf-8")
        if data is None or not isinstance(data, bytes):
            raise NotImplementedError("Data type not supported")
        result_hash_val = hashlib.md5(data).hexdigest()
        self.hash_check_log(result_hash_val, hash_val)

    def save_ref(self, name: str, data: bytes):
        """
        Saves a new data reference

        :param name: The reference's unique name
        :param data: The data to store
        """
        hashed_name = self._get_hashed_filename(name)
        os.makedirs(self.ref_dir, exist_ok=True)
        hash_fn = self.ref_dir + "/" + hashed_name + ".dmp"
        FileStag.save(hash_fn, data)

    def load_ref(self, name: str) -> bytes | None:
        """
        Loads the data reference

        :param name: The reference's unique name
        :return: The data. None if no reference could be found
        """
        hashed_name = self._get_hashed_filename(name)
        hash_fn = self.ref_dir + "/" + hashed_name + ".dmp"
        if FileStag.exists(hash_fn):
            return FileStag.load(hash_fn)
        return None

    def _get_hashed_filename(self, name):
        """
        Returns a hashed filename for name to be store it with a fixed size
        on disk

        :param name: The file's name
        :return: The hash name to be used as filename
        """
        hashed_name = hashlib.md5(name.encode('utf-8')).hexdigest()
        return hashed_name

    def _html_linebreaks(self, text: str) -> str:
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
        if HTML not in self._logs:
            return
        self._logs[HTML].append(html_code.encode("utf-8"))
        if self.continuous_write:
            self.write_to_disk(formats={HTML})
        return True

    def _add_md(self, md_code: str, no_break: bool = False):
        """
        The markdown code to add

        :param md_code: The markdown code
        :param no_break: If defined no line break will be added
        :return: True if txt logging is enabled
        """
        if MD not in self._logs:
            return
        new_text = md_code + ("" if no_break else "\n")
        self._logs[MD].append(new_text.encode("utf-8"))
        if self.continuous_write:
            self.write_to_disk(formats={MD})
        return True

    def _add_txt(self, txt_code: str, console: bool = True, md: bool = False):
        """
        Adds text code to the txt / console log

        :param txt_code: The text to add
        :param console: Defines if the text shall also be added ot the
            console's log (as it's mostly identical). True by default.
        :param md: Defines if the text shall be added to markdown as well
        :return: True if txt logging is enabled
        """
        if console and len(self._consoles):
            self._add_to_console(txt_code)
        if md and MD in self._logs:
            self.md(txt_code)
        if TXT not in self._logs:
            return
        self._logs[TXT].append((txt_code + "\n").encode("utf-8"))
        if self.continuous_write:
            self.write_to_disk(formats={TXT})
        return True

    def _add_to_console(self, txt_code: str):
        """
        Adds text code to the console log

        :param txt_code: The text to add
        :return: True if txt logging is enabled
        """
        for console in self._consoles:
            if console.progressive and len(self._log_stag) == 1:
                console.print(txt_code)
        self._logs[CONSOLE].append((txt_code + "\n").encode("ascii"))
        return True

    def get_temp_path(self, relative: str | None = None) -> str:
        """
        Returns the temporary file path. The data will be wiped upon the call
        of finalize.

        :param relative: A relative path which can be passed and automatically
            gets concatenated.
        :return: The path or combined path
        """
        os.makedirs(self._tmp_path, exist_ok=True)
        if relative is not None:
            return FilePath.norm_path(self._tmp_path + "/" + relative)
        return self._tmp_path

    def _build_body(self, base_log: dict[str:bytes]):
        """
        Requests to combine all logs and sub logs to a single page which
        can be logged to the disk or provided in the browser. (excluding
        html headers and footers), so just "the body" of the HTML page.

        :param base_log: The byte stream of all concatenated logs for each
            output type.
        :return: The finalized page, e.g. by combining base_log w/
            sub_logs as shown in the :class:`VisualLiveLog` class.
        """
        body: dict[str, bytes] = {}
        for cur_format, log_entries in base_log.items():
            body[cur_format] = b"".join(log_entries)

        for cur_format in self._log_formats:
            sub_log_data = {MAIN_LOG: b"".join(self._logs[cur_format])}
            for sl_key, sl_data in self.sub_log_data.items():
                if cur_format in sl_data:
                    sub_log_data[sl_key] = sl_data[cur_format]

            if cur_format == HTML:
                body[cur_format] = \
                    self._renderers[HTML].build_body(
                        sub_log_data)
        return body

    def flush(self):
        """
        Writes the current state to disk
        """
        self.write_to_disk()

    def set_latest_page(self, page_type: str, content: bytes):
        """
        Stores a copy of the latest page.

        This method is multi-threading secure.

        :param page_type: The format of the page to store
        :param content: The page's new content
        """
        with self._page_lock:
            self._page_backups[page_type] = content

    def get_page(self, format_type: str) -> bytes:
        """
        Receives the newest update of the page of given output type.

        If not done automatically (e.g. when using a VisualLiveLog)
        you might have to call render_pages yourself.

        This method is multi-threading secure.

        Assumes that render() or write_to_disk() or render was called before
        since the last change. This is not necessary if continuous_write is
        enabled.

        :param format_type: The type of the page you want to receive
        :return: The page's content.
        """
        with self._page_lock:
            if format_type in self._page_backups:
                return self._page_backups[format_type]
            return b""

    def get_body(self, format_type: str) -> bytes:
        """
        Returns the latest body data.

        Contains only the part of that format w/ header and footer.
        Can be used to for example embed one log's content in another log
        such as main_log.html(sub_log.get_body("html"))

        Assumes that render() or write_to_disk() or render was called before
        since the last change. This is not necessary if continuous_write is
        enabled.

        :param format_type: The type of the page you want to receive
        :return: The page's content.
        """
        with self._page_lock:
            if format_type in self._body_backups:
                return self._body_backups[format_type]
            return b""

    def render(self, formats: set[str] | None = None) -> VisualLog:
        """
        Renders all pages - so combines the main log with the sub logs
        of the supported output types (html, txt, md etc.) and stores
        them.

        The page data for each type can be received via :meth:`get_latest_page`.

        :param formats: A set of the formats which shall be rendered.

            None = All configured formats.
        :return: The VisualLog object
        """
        if formats is None:
            formats = self._log_formats
        bodies = self._build_body(self._logs)
        with self._page_lock:
            self._body_backups = bodies
        # store html
        if self._html_export and self._html_filename is not None and len(
                self._html_filename) > 0 and HTML in formats:
            self.set_latest_page(HTML,
                                 self._renderers[HTML].build_page(bodies[HTML]))
        # store markdown
        if self._md_export and self._md_filename is not None and \
                len(self._md_filename) > 0 and MD in formats:
            self.set_latest_page(MD, bodies[MD])
        # store txt
        if self._txt_export and self._txt_filename is not None and \
                len(self._txt_filename) > 0 and TXT in formats:
            self.set_latest_page(TXT, bodies[TXT])
        if CONSOLE in formats:
            for console in self._consoles:
                if console.progressive:
                    continue
                console.clear()
                body = bodies[CONSOLE]
                console.print(body.decode("ascii"))
        return self

    def write_to_disk(self, formats: set[str] | None = None,
                      render=True) -> VisualLog:
        """
        Writes the rendered pages from all (or all specified) formats to
        disk.

        :param formats: A set of formats to write. None = all configured

            e.g. {"html, "txt") etc. By default all formats will be stored.
        :param render: Defines if the pages shall be rendered (if necessary)
        :return: The VisualLog object
        """
        if formats is None:
            formats = self._log_formats

        if render:
            self.render(formats=formats)

        if self._log_to_disk:
            # store html
            if self._html_export and self._html_filename is not None and \
                    len(self._html_filename) > 0 and HTML in formats:
                FileStag.save(self._html_filename,
                              self.get_page(HTML))
                # store markdown
            if self._md_export and self._md_filename is not None and \
                    len(self._md_filename) > 0 and MD in formats:
                FileStag.save(self._md_filename, self.get_page(MD))
            # store txt
            if self._txt_export and self._txt_filename is not None and \
                    len(self._txt_filename) > 0 and TXT in formats:
                FileStag.save(self._txt_filename,
                              self.get_page(TXT))
        return self

    def finalize(self) -> VisualLog:
        """
        Finalizes the report and writes it to disk

        :return: The VisualLog object
        """
        self.write_to_disk(render=True)
        if FilePath.exists(self._tmp_path):
            shutil.rmtree(self._tmp_path)
        return self

    def create_web_service(self, support_flask: bool = False,
                           url_prefix: str = "") -> "WebStagService":
        """
        Creates a web service which provides (for example) a blueprint you
        can add to an arbitrary Flask server.

        :param support_flask: Support Flask (and setup a blueprint?)
        :param url_prefix: The url prefix at which the service shall be hosted.

            "" = At http://server
            "log/" = At http://server/log
        :return: The service object containing the services for the
            request backends (e.g. flask, fastapi etc.)
        """
        from scistag.webstag.server import WebClassService
        service = WebClassService("VisualLogService", url_prefix=url_prefix,
                                  support_flask=support_flask)
        service.add_class(VisualLogService, service_name="",
                          parameters={"log": self})
        return service

    def run_server(self,
                   host_name: str = "127.0.0.1",
                   port: int | tuple[int, int] = 8010,
                   url_prefix: str = "",
                   public_ips: str | list[str] | None = None,
                   builder: BuilderTypes | None = None,
                   continuous: bool | None = None,
                   wait: bool = False,
                   auto_clear: bool | None = None,
                   overwrite: bool | None = None,
                   mt: bool = False,
                   test: bool = False,
                   server_logs: bool = False,
                   show_urls: bool = True,
                   auto_reload=False,
                   auto_reload_stag_level: 1 = 1,
                   **kwargs):
        """
        Hosts the log as web service.

        This way you can either provide the log as a static website or
        even update it dynamically and

        :param host_name: The IP(s) to listen at.

            - 127.0.0.1 = Local access only (default) as
              "there is no place like localhost".
            - "0.0.0.0" = Listen at all local network adapters
        :param port: The port ot listen at or a port range to select the
            first port within. 8010 by default. 0 for a random port.
        :param url_prefix: The url prefix at which the service shall be hosted.

            "" = At http://server
            "log/" = At http://server/log
        :param public_ips: If you run the service on a virtual machine in
            the cloud you can pass its public IPs to log the correct
            connection URls to the console.

            If you pass "auto" as ip the public IP will be auto-detected via
            ipify.
        :param builder: An (optional) function to be called to build or
            (repetitively) rebuild the log's content.

            The function can be called once - if continuous=False was passed,
            continuously with a frequency of :attr:`refresh_time_s`
            (as passed to the constructor) if continuous=True was passed.

            Instead of passing a builder callback you can as well as also
            just fill the log with content before running :meth:`run_server`.
        :param continuous: Defines if the run_server shall run until
            :meth:`terminate` was called to update the logs content
            continuously.

            False by default.
        :param wait: Defines if also a non-continuous log shall wait till
            the log has been terminated. (via :meth:`terminate`) or the
            application was killed via Ctrl-C.

            Has no effect if threaded is False (because the server will anyway
            block the further execution then) or if continuous is set to True.

            Basically it acts like the "continuous" mode just with the
            difference that the builder function is just called once.
        :param auto_clear: Defines if then log shall be cleared automatically
            when being rebuild with `continuous=True`.
        :param overwrite: If set to False it will only call the `builder`
            function if there is no recent version of the log stored on
            disk.

            This way you can host the log results of a (potentially)
            long-running data engineering or ML training session without
            accidentally re-running it.
        :param mt: If set to true the server will be started in a
            background thread and the method will return asap.

            You have to pass `mt=True` if this log shall be updated
            `continuous`ly.

            If the log is dynamic, but you do not want to be stuck in this
            function you can - instead of passing a builder - (optionally) just
            call :meth:`clear_logs` to clear the log and when you are done
            updating the log :meth:`write_to_disk` or just :meth:`render`
            the update the page provided by the server,

            Example:

            ..  code-block: python

                vl = VisualLog()
                while True:
                    vl.clear_logs()
                    vl.text(time.time())
                    vl.write_to_disk()
                    time.sleep(vl.refresh_time_s)
        :param test: Defines if the server shall be created in test mode
            (just "virtually")
        :param server_logs: Defines if the Flask and/or FastAPI logs shall
            be enabled.
        :param show_urls: Defines if the URLs at which the server can be
            reached shall be shown upon start
        :param auto_reload: If swt to True the module calling this function
            will automatically be reloaded on-the-fly when ever it is
            modified and saved and the log will be rebuilt from scratch.

            Note that this will override many of the other objects specified
            in the call of this function such as

            - mt - As multithreading is required to use this feature
            - continous - which is is currently not supported yet.
            - ...
        :param auto_reload_stag_level: Defines which module shall be observed
            and reloaded upon modifications.

            By default it is the method of the calling module (1). If you need
            e.g. to track the caller's caller (2) increase this number
            accordingly.
        :param kwargs: Additional parameters which shall be passed to the
            WebStagServer upon creation.
        """
        self._start_time = time.time()
        if not isinstance(auto_reload, bool) or auto_reload:
            from scistag.logstag.visual_log.visual_log_autoreloader import \
                VisualLogAutoReloader
            if continuous:
                raise NotImplementedError(
                    "Continuous mode is not supported yet by auto-reload")
            self._run_builder(builder)
            self.handle_event_list()
            VisualLogAutoReloader.start(log=self,
                                        host_name=host_name,
                                        port=port,
                                        public_ips=public_ips,
                                        url_prefix=url_prefix,
                                        _stack_level=auto_reload_stag_level + 1
                                        )
            return
        from scistag.webstag.server import WebStagServer
        service = self.create_web_service(support_flask=True,
                                          url_prefix=url_prefix)
        server = WebStagServer(host_name=host_name,
                               port=port,
                               services=[service],
                               silent=not server_logs,
                               **kwargs)
        port = server.port
        self._server = server
        if continuous is not None:
            if builder is None:
                raise ValueError(_CONTINUOUS_NO_EFFECT_WITHOUT_BUILDER)
            if not continuous:
                if auto_clear is not None and auto_clear:
                    raise ValueError(_ONLY_AUTO_CLEAR_ON_CONTINUOUS)
            else:
                if not mt or test:
                    raise ValueError(_CONTINUOUS_REQUIRED_BG_THREAD)
                if overwrite is not None and not overwrite:
                    raise ValueError(_CONTINUOUS_REQUIRES_OVERWRITE)
        else:
            continuous = False
        if public_ips is not None:  # clean public IPs
            if isinstance(public_ips, str):
                public_ips = [public_ips]
        else:
            public_ips = [host_name]
            if host_name != "127.0.0.1" and host_name != "localhost":
                public_ips.append("localhost")
        # auto-detect public if "auto" is passed
        for index, element in enumerate(public_ips):
            if element == "auto":
                public_ips[index] = WebHelper.get_public_ip()
        # show URLs if desired
        if show_urls:
            print("\nVisualLog web service started\n")
            print("Connect at:")
            for cur_ip in public_ips:
                print(
                    f"* http://{cur_ip}:{port}{url_prefix} for the static log")
                print(
                    f"* http://{cur_ip}:{port}{url_prefix}/live for "
                    f"the auto-reloader")
                print('\n')
        overwrite = overwrite if overwrite is not None else True
        if not continuous and not mt:  # if the server will block execute
            # once here, otherwise after the server started
            if builder is not None:  # call once
                if overwrite is True or not self.load_old_logs():
                    self._run_builder(builder)
                    self.handle_event_list()
                    self.write_to_disk()
        server.start(mt=mt, test=test)
        if continuous:
            auto_clear = auto_clear if auto_clear is not None else True
            self._run_continuous(auto_clear, builder)
        elif mt:
            if builder is not None:  # call once
                if overwrite is True or not self.load_old_logs():
                    self._run_builder(builder)
                    self.handle_event_list()
                    self.write_to_disk()
            if wait:
                self.sleep()

    def run(self,
            builder: BuilderCallback,
            continuous: bool | None = None,
            auto_clear: bool | None = None,
            overwrite: bool | None = None,
            auto_reload: bool = False
            ) -> bool:
        """
        Helper function to update the log via a callback function.

        This helps you to
        - Create the log only once when it was not yet created.

          Pass `overwrite=False`.
        - Run the method `continuous`ly and update or extend it on disk with a
            defined frequency.
        - When run in "continuous"-mode:
            - To just extend the log use auto_clear = False
            - To completely rewrite the log every turn pass auto_clear = True

        :param builder: The function to be called to build or
            (repetitively) rebuild the log's content.

            The function can be called once - if continuous=False was passed,
            continuously with a frequency of :attr:`refresh_time_s`
            (as passed to the constructor) if continuous=True was passed.
        :param continuous: Defines if the run_server shall run until
            :meth:`terminate` was called to update the logs content
            continuously and write them to disk each turn.

            False by default.
        :param auto_clear: Defines if then log shall be cleared automatically
            when being rebuild with `continuous=True`.
        :param overwrite: If set to False it will only call the `builder`
            function if there is no recent version of the log stored on
            disk.

            If a valid log was found the `builder` method passed will never
            be called.
        :param auto_reload: If swt to True the module calling this function
            will automatically be reloaded on-the-fly when ever it is
            modified and saved and the log will be rebuilt from scratch.

            Note that this will override many of the other objects specified
            in the call of this function such as

            - mt - As multithreading is required to use this feature
            - continous - which is is currently not supported yet.
            - ...
        :return: False if overwrite=False was passed and a log
            could successfully be loaded, so that no run was required.
        """
        self._start_time = time.time()
        if not isinstance(auto_reload, bool) or auto_reload:
            from scistag.logstag.visual_log.visual_log_autoreloader import \
                VisualLogAutoReloader
            if continuous:
                raise NotImplementedError(
                    "Continuous mode is not supported yet by auto-reload")
            self._run_builder(builder)
            self.handle_event_list()
            VisualLogAutoReloader.start(log=self,
                                        host_name=None,
                                        _stack_level=2)
            return
        if continuous is None:
            continuous = False
        if builder is None:
            raise ValueError("Passing a builder is required")
        if not continuous:
            if auto_clear is not None and auto_clear:
                raise ValueError(_ONLY_AUTO_CLEAR_ON_CONTINUOUS)
        else:
            if overwrite is not None and not overwrite:
                raise ValueError(_CONTINUOUS_REQUIRES_OVERWRITE)
        if not continuous:
            overwrite = overwrite if overwrite is not None else True
            if builder is not None:  # call once
                if overwrite is True or not self.load_old_logs():
                    self._run_builder(builder)
                    self.handle_event_list()
                    self.write_to_disk()
                else:
                    return False
        if continuous:
            auto_clear = auto_clear if auto_clear is not None else True
            self._run_continuous(auto_clear, builder)
        return True

    def _run_builder(self, builder: BuilderTypes | None = None):
        """
        Runs the associated builder

        :param builder: The builder to be called from rebuild the log
        """
        if builder is not None:
            builder(self)
        self.write_to_disk()

    def kill_server(self) -> bool:
        """
        Kills the http server running in the background.

        If you hosted this log as a webserver running in the background using
        run_server(mt=True) you can use this method to (by force) kill the
        server being used. Note that this may lead to memory leaks and should
        only be used to really shut down an application and to for example
        prevent Flask keeping the process alive upon Ctrl-C.

        :return: True on success
        """
        if self.server is None:
            raise AssertionError("Server not started, nothing to shut down")
        return self.server.kill()

    def sleep(self):
        """
        Sleeps and handles input events until the application is either
        terminated by Ctrl-L or by an exit button added to the log or a quit
        call triggered.
        """
        print("\nZzzzzzz - Press Ctrl-C to terminate\n")
        while not self._shall_terminate:
            time.sleep(self.refresh_time_s)

    def _run_continuous(self, auto_clear: bool,
                        builder: BuilderCallback):
        """
        Runs the builder until :meth:`terminate` is called.

        :param auto_clear: Defines if the log shall be cleared each turn
        :param builder: The builder function to call
        """
        self._start_time = time.time()
        next_update = time.time()
        while True:
            self._update_counter += 1
            self._total_update_counter += 1
            with self._page_lock:
                if self._shall_terminate:
                    break
            if auto_clear:
                self.clear_logs()
            self._run_builder(builder)
            self.handle_event_list()
            self.write_to_disk()
            cur_time = time.time()
            while cur_time < next_update:
                time.sleep(next_update - cur_time)
                cur_time = time.time()
            # try to keep the frequency but never build up debt:
            next_update = max(next_update + self.refresh_time_s, cur_time)
            self._update_statistics(cur_time)

    @property
    def server(self) -> "WebStagServer":
        """
        Returns the server (if one was created) and started via
        :meth:`run_server`.
        """
        return self._server

    @property
    def cache(self) -> Cache:
        """
        Returns the log's cache object to cache computation data between
        functions repetitions or even multiple execution sessions.
        """
        return self._cache

    def _update_statistics(self, cur_time: float):
        """
        Updates the statistics if necessary

        :param cur_time: The current system time (in seconds)
        """
        # update once per second if fps is high, otherwise once all x seconds
        update_frequency = (1.0 if self._update_rate == 0.0
                                   or self._update_rate > 20 else 5.0)
        if cur_time - self._last_statistic_update > update_frequency:
            time_diff = cur_time - self._last_statistic_update
            self._update_rate = self._update_counter / time_diff
            self._last_statistic_update = cur_time
            self._update_counter = 0

    def _setup_cache(self, auto_reload, cache_version, cache_dir, cache_name):
        """
        Configures the data cache

        :param auto_reload: Auto-reloading used?
        :param cache_version: The cache version. 1 by default.

            When ever you change this version all old cache values will be
            removed and/or ignored from the cache.
        :param cache_dir: The cache target directory on disk
        :param cache_name: The unique name of the cache, e.g. for the case
            multiple logs use the same logging directory
        """
        if len(cache_name) > 0:
            cache_name = f"{cache_name}/"
        if cache_dir is None:
            cache_dir = \
                f"{os.path.abspath(self.target_dir)}/.stscache/{cache_name}"
        else:
            cache_dir = f"{cache_dir}/{cache_name}"
        auto_reload_cache = None
        if auto_reload:  # if auto-reloading is enabled try to restore cache
            # check if there is a valid, prior cache available
            from .visual_log_autoreloader import VisualLogAutoReloader
            auto_reload_cache = VisualLogAutoReloader.get_cache_backup()
            if auto_reload_cache is not None and \
                    auto_reload_cache.version != cache_version:
                auto_reload_cache = None
        self._cache = Cache(cache_dir=cache_dir,
                            version=cache_version,
                            ) if auto_reload_cache is None \
            else auto_reload_cache

    def add_event(self, event):
        """
        Adds an event to the event queue which will be handled before and
        after the next re-build (or loop turn in case of a continuous log).

        :param event: The new event
        """
        with self._page_lock:
            self._events.append(event)
            self.cache.set(LOG_EVENT_CACHE_NAME, self._events)

    def handle_event_list(self):
        """
        Handles all queued events and clears the event queue
        """
        event_list = []
        with self._page_lock:
            event_list = self._events
            self._events = []
            self.cache.set(LOG_EVENT_CACHE_NAME, self._events)
        for element in event_list:
            self.handle_event(element)

    def handle_event(self, event: "LogEvent"):
        """
        Handles a single event and forwards it to the correct widget

        :param event: The event to be handled
        """
        if event.name in self._widgets:
            self._widgets[event.name].handle_event(event)

    def get_events(self, clear: bool = False) -> list["LogEvent"]:
        """
        Returns the current list of events

        :param clear: Defines if all events shall be removed afterwards
        :return: The event list
        """
        with self._page_lock:
            event_list = list(self._events)
            if clear:
                self._events = []
                self.cache.set(LOG_EVENT_CACHE_NAME, self._events)
            return event_list

    def register_widget(self, name: str, widget: "LogWidget"):
        """
        Registers a widget which is able to receive events

        :param name: The name of the widget to register
        :param widget: The widget
        """
        self._widgets[name] = widget

    def add_button(self,
                   name: str,
                   caption: str,
                   on_click: Callable | None = None) -> "LogButton":
        """
        Adds a button to the log which can be clicked and raise a click event.

        :param name: The button's name
        :param caption: The button's caption
        :param on_click: The function to be called when the button is clicked
        :return: The button widget
        """
        from scistag.logstag.visual_log.widgets.log_button import LogButton
        new_button = LogButton(self, name, caption=caption, on_click=on_click)
        new_button.write()
        return new_button

    def invalidate(self):
        """
        Flag this log as invalidate for inform the auto-reloader that this
        log should be reloaded
        """
        self._invalid = True

    @property
    def invalid(self) -> bool:
        """
        Returns if this log was invalidated and should be rebuilt
        """
        return self._invalid

    @classmethod
    def is_main(cls) -> bool:
        """
        Returns if the file calling this method was the main entry point
        before the module got reloaded.

        Only available if auto-reloading is being used.

        :return: True if the calling method is in the main module.
        """
        from scistag.logstag.visual_log.visual_log_autoreloader import \
            VisualLogAutoReloader
        return VisualLogAutoReloader.is_main(2)

    @staticmethod
    def setup_mocks(target_dir: str = "./"):
        """
        Creates a set of files in the defined directory which contain
        replacements for the essential logging classes such as VisualLog,
        VisualLogBuilder etc. which can be used on systems without
        a valid SciStag installation such as MicroPython.

        ..  code-block:python

            try:
                from scistag.logstag import VisualLog, VisualLogBuilder
                VisualLog.setup_mocks()
            except ModuleNotFoundError:
                from visual_log_mock import VisualLog, VisualLogBuilder
        """
        from .visual_log_mock import VisualLogMock
        VisualLogMock.setup_mocks(target_dir)

    @property
    def is_simple(self) -> bool:
        """
        Returns if this builder is a minimalistic logger with limited functionality.

        See :meth:`setup_mocks`

        :return: True if it is a mock
        """
        return False
