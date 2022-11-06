"""
Helper functions to export images of rendering methods for manual verification
"""
from __future__ import annotations

import builtins
import os
import shutil
import time
from collections import Counter
from typing import TYPE_CHECKING, Callable, Union, Type

from scistag.common import StagLock, Cache
from scistag.filestag import FileStag, FilePath
from scistag.imagestag import Size2D, Size2DTypes
from scistag.logstag.vislog.visual_log_service import VisualLogService
from scistag.webstag.web_helper import WebHelper
from ..console_stag import Console
from .sub_log import SubLog, SubLogLock

if TYPE_CHECKING:
    from scistag.webstag.server import WebStagServer
    from scistag.webstag.server import WebStagService
    from .visual_log_renderer import VisualLogRenderer
    from .visual_log_renderer_html import VisualLogHtmlRenderer
    from .widgets.log_widget import LogWidget
    from .widgets.log_button import LogButton
    from .visual_log_builder import VisualLogBuilder
    from .visual_log_statistics import VisualLogStatistics
    from scistag.logstag.vislog.log_event import LogEvent

# Error messages
TABLE_PIPE = "|"
"Defines the character which starts and ends an ASCII table in a log file"

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

# Definition of output types
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

BuilderCallback = Callable[["VisualLogBuilder"], None]
"""
Type definition for a function which can be passed to VisualLog's initializer
to be called once or continuously to update the log.
"""

BuilderTypes = Union[
    BuilderCallback, "VisualLogBuilder", Type["VisualLogBuilder"]]
"""
The supported builder callback types.
 
Either a function which can be called, a VisualLogBuilder object provided by
the user or a class of a VisualLogBuilder ancestor class of which we shall
created an instance.
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

    def __init__(self, title: str = "SciStag - VisualLog",
                 target_dir: str = "./logs",
                 formats_out: set[str] | None = None,
                 ref_dir: str | None = None,
                 tmp_dir: str | None = None,
                 clear_target_dir: bool = False,
                 log_to_disk=True,
                 log_to_stdout=True,
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
        :param log_to_stdout: Defines if the system shall automatically log to
            stdout via print as well
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
        do_auto_reload = (isinstance(auto_reload, bool) and auto_reload
                          or auto_reload is not None)
        self._setup_cache(do_auto_reload, cache_version, cache_dir, cache_name)
        self.ref_dir = FilePath.norm_path(
            self.target_dir + "/ref" if ref_dir is None else ref_dir)
        "The directory in which reference files for comparison shall be stored"
        self.tmp_path = FilePath.norm_path(
            self.target_dir + "/temp" if tmp_dir is None else tmp_dir)
        "Output directory for temporary files"
        if log_to_disk:
            os.makedirs(self.target_dir, exist_ok=True)
        self.log_to_disk = log_to_disk
        "Defines if the images and the html data shall be written to disk"
        self.log_images = True
        "Defines if images shall be logged to disk"
        self.refresh_time_s = refresh_time_s
        """
        The time interval with which the log shall be refreshed when using
        the liveViewer (see Live_view)
        """
        if max_fig_size is not None and not isinstance(max_fig_size, Size2D):
            max_fig_size = Size2D(max_fig_size)
        else:
            max_fig_size = Size2D(1024, 1024)
        "Defines the preview's width and height"
        self.log_formats = formats_out
        "Defines if text shall be logged"
        self.log_formats.add(CONSOLE)
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
                                              sorted(self.log_formats)}
        """
        Contains the log data for each output type
        """
        self._log_stag.append(SubLog(logs=self._logs, target="",
                                     max_fig_size=max_fig_size.to_int_tuple()))
        self.continuous_write = continuous_write
        "If defined the output logs will be updated after every log"
        self.markdown_html = True
        "Defines if markdown shall support html embedding"
        self.log_txt_images = True
        "Defines if images shall also be logged to text files as ASCII"
        self.use_tabulate = True
        "Defines if tabulate may be used"
        self.use_pretty_html_table = True
        "Defines if pretty html shall be used"
        self.html_table_style = 'blue_light'
        "The pretty html style to be used"
        self.txt_table_format = "rounded_outline"
        "The text table format to use in tabulate"
        self.md_table_format = "github"
        "The markdown table format to use"
        self.embed_images = (embed_images if embed_images is not None else
                             MD not in formats_out)
        if isinstance(image_format, tuple):  # unpack tuple if required
            image_format, image_quality = image_format
        "If defined images will be embedded directly into the HTML code"
        self.image_format = image_format
        "The default image type to use for storage"
        self.image_quality = image_quality
        "The image compression quality"
        self._html_export = HTML in self.log_formats
        "Defines if HTML gets exported"
        self.md_export = MD in self.log_formats
        "Defines if markdown gets exported"
        self.txt_export = TXT in self.log_formats
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
        self.start_time = time.time()
        "The time stamp of when the log was creation"
        self._events = []
        "List of unhandled events"
        self._widgets = {}
        "Set of widgets"
        self.log_to_stdout = log_to_stdout
        "Defines if all log messages shall also be send to stdout via print"
        if do_auto_reload:
            self._events = self.cache.get(LOG_EVENT_CACHE_NAME, default=[])
        self._invalid = False
        "Defines if this log was invalidated via :meth:`invalidate`"
        # execute auto-reloader if provided
        if not isinstance(auto_reload, bool) and auto_reload is not None:
            self.run_server(host_name="127.0.0.1",
                            builder=auto_reload, auto_reload=True,
                            auto_reload_stag_level=2)
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
        from .visual_log_builder import VisualLogBuilder
        self.default_builder: VisualLogBuilder = VisualLogBuilder(self)
        """
        The default builder. It let's you easily add content the log without
        the need of any callbacks.
        
        ..  code-block: python
        
            log = VisualLog()
            vl = log.default_builder
            vl.title("Hello world")
            
            # or for the especially lazy ones
            with VisualLog() as vl:
                v.title("Hello world') 
        """

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

    def _provide_live_view(self):
        """
        Assembles a website file which automatically updates the
        logged html file as often as possible when ever it is updated
        on disk.
        """
        base_path = self._get_module_path()
        css = FileStag.load(base_path + "/css/visual_log.css")
        if self.log_to_disk:
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
                                          self.refresh_time_s * 1000),
                                      reload_url="index.html")
        if self.log_to_disk:
            FileStag.save_text(self.target_dir + "/liveView.html",
                               rendered_lv)
        rendered_lv = template.render(title=self._title,
                                      reload_timeout=2000,
                                      retry_frequency=100,
                                      reload_frequency=int(
                                          self.refresh_time_s * 1000),
                                      reload_url="index")
        self.add_static_file('liveView.html',
                             rendered_lv.encode("utf-8"))

    def write_html(self, html_code: str):
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

    def write_md(self, md_code: str, no_break: bool = False):
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

    def write_txt(self, txt_code: str, console: bool = True, md: bool = False):
        """
        Adds text code to the txt / console log

        :param txt_code: The text to add
        :param console: Defines if the text shall also be added ot the
            console's log (as it's mostly identical). True by default.
        :param md: Defines if the text shall be added to markdown as well
        :return: True if txt logging is enabled
        """
        if self.log_to_stdout:
            print(txt_code)
        if console and len(self._consoles):
            self._add_to_console(txt_code)
        if md and MD in self._logs:
            self.write_md(txt_code)
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
        os.makedirs(self.tmp_path, exist_ok=True)
        if relative is not None:
            return FilePath.norm_path(self.tmp_path + "/" + relative)
        return self.tmp_path

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

        for cur_format in self.log_formats:
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
            formats = self.log_formats
        bodies = self._build_body(self._logs)
        with self._page_lock:
            self._body_backups = bodies
        # store html
        if self._html_export and self._html_filename is not None and len(
                self._html_filename) > 0 and HTML in formats:
            self.set_latest_page(HTML,
                                 self._renderers[HTML].build_page(bodies[HTML]))
        # store markdown
        if self.md_export and self._md_filename is not None and \
                len(self._md_filename) > 0 and MD in formats:
            self.set_latest_page(MD, bodies[MD])
        # store txt
        if self.txt_export and self._txt_filename is not None and \
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
            formats = self.log_formats

        if render:
            self.render(formats=formats)

        if self.log_to_disk:
            # store html
            if self._html_export and self._html_filename is not None and \
                    len(self._html_filename) > 0 and HTML in formats:
                FileStag.save(self._html_filename,
                              self.get_page(HTML))
                # store markdown
            if self.md_export and self._md_filename is not None and \
                    len(self._md_filename) > 0 and MD in formats:
                FileStag.save(self._md_filename, self.get_page(MD))
            # store txt
            if self.txt_export and self._txt_filename is not None and \
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
        if FilePath.exists(self.tmp_path):
            shutil.rmtree(self.tmp_path)
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
                   wait: bool = True,
                   auto_clear: bool | None = None,
                   overwrite: bool | None = None,
                   mt: bool = True,
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
        if builder is not None:
            builder = self.prepare_builder(builder)
        self.start_time = time.time()
        if not isinstance(auto_reload, bool) or auto_reload:
            from scistag.logstag.vislog.visual_log_autoreloader import \
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
        if builder is not None:
            builder = self.prepare_builder(builder)
        self.start_time = time.time()
        if not isinstance(auto_reload, bool) or auto_reload:
            from scistag.logstag.vislog.visual_log_autoreloader import \
                VisualLogAutoReloader
            if continuous:
                raise NotImplementedError(
                    "Continuous mode is not supported yet by auto-reload")
            self._run_builder(builder)
            self.handle_event_list()
            VisualLogAutoReloader.start(log=self,
                                        host_name=None,
                                        _stack_level=2)
            return True
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
            if getattr(builder, "build", None) is not None:
                builder.build()
            else:
                builder(self.default_builder)
        self.write_to_disk()

    def prepare_builder(self, builder: BuilderTypes):
        """
        Prepapres the builder to be used for this log

        :param builder: The build helper, either a function which fills the
            log or an ancestor of VisualLogBuilder implementing at least the
            build_body method to do the same.
        :return: The prepared build object
        """
        if isinstance(builder, type):
            builder: Type[VisualLogBuilder] | VisualLogBuilder
            builder = builder(log=self)
            from .visual_log_builder import VisualLogBuilder
            if not isinstance(builder, VisualLogBuilder):
                raise ValueError("No valid VisualLogBuilder base "
                                 "class provided")
        return builder

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
        self.start_time = time.time()
        next_update = time.time()
        while True:
            self._update_counter += 1
            self._total_update_counter += 1
            with self._page_lock:
                if self._shall_terminate:
                    break
            if auto_clear:
                self.clear()
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
        update_frequency = (1.0 if (self._update_rate == 0.0 or
                                    self._update_rate > 20) else 5.0)
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
                   on_click: Union[Callable, None] = None) -> "LogButton":
        """
        Adds a button to the log which can be clicked and raise a click event.

        :param name: The button's name
        :param caption: The button's caption
        :param on_click: The function to be called when the button is clicked
        :return: The button widget
        """
        from scistag.logstag.vislog.widgets.log_button import LogButton
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

    def get_statistics(self) -> "VisualLogStatistics":
        """
        Returns statistics about the log

        :return: A dictionary with statistics about the log such as
            - totalUpdateCount - How often was the log updated?
            - updatesPerSecond - How often was the log updated per second
            - upTime - How long is the log being updated?
        """

        from scistag.logstag.vislog.visual_log_statistics import \
            VisualLogStatistics
        return VisualLogStatistics(update_counter=self._total_update_counter,
                                   update_rate=self._update_rate,
                                   uptime=time.time() - self.start_time)

    def embed(self, log_data: VisualLog):
        """
        Embeds another VisualLog's content into this one

        :param log_data: The source log
        """
        for cur_format in self.log_formats:
            if cur_format in log_data.log_formats:
                self._logs[cur_format].append(log_data.get_body(cur_format))

    def clear(self):
        """
        Clears the whole log (excluding headers and footers)
        """
        self.name_counter = Counter()
        self.title_counter = Counter()
        for key in self._logs.keys():
            self._logs[key].clear()

    @classmethod
    def is_main(cls) -> bool:
        """
        Returns if the file calling this method was the main entry point
        before the module got reloaded.

        Only available if auto-reloading is being used.

        :return: True if the calling method is in the main module.
        """
        from scistag.logstag.vislog.visual_log_autoreloader import \
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
                from scistag.logstag.vislog import VisualLog, VisualLogBuilder
                VisualLog.setup_mocks()
            except ModuleNotFoundError:
                from visual_log_mock import VisualLog, VisualLogBuilder
        """
        from .visual_log_mock import VisualLogMock
        VisualLogMock.setup_mocks(target_dir)

    @property
    def is_simple(self) -> bool:
        """
        Returns if this builder is a minimalistic logger with limited
        functionality.

        See :meth:`setup_mocks`

        :return: True if it is a mock
        """
        return False

    def reserve_unique_name(self, name: str):
        """
        Reserves a unique name within the log, e.g. to store an object to
        a unique file.

        :param name: The desired name
        :return: The effective name with which the data shall be stored
        """
        self.name_counter[name] += 1
        result = name
        if self.name_counter[name] > 1:
            result += f"_{self.name_counter[name]}"
        return result

    def __enter__(self) -> "VisualLogBuilder":
        """
        Returns the default builder

        ..  code-block:

            with VisualLog() as vl:
                vl.title("Hello world")

        :return: The builder object
        """
        return self.default_builder


__all__ = ["VisualLog", "VisualLogStatistics"]
