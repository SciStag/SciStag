"""
Helper functions to export images of rendering methods for manual verification
"""
from __future__ import annotations

import os
import shutil
import time
from typing import TYPE_CHECKING, Callable, Union, Type, Literal

import scistag
from scistag.common import StagLock, Cache, StagApp
from scistag.filestag import FileStag, FilePath
from scistag.imagestag import Size2D, Size2DTypes
from scistag.webstag.web_helper import WebHelper
from scistag.logstag.console_stag import Console
from scistag.vislog.sessions.page_session import PageSession, HTML, MD, TXT, CONSOLE

if TYPE_CHECKING:
    from scistag.webstag.server import WebStagServer
    from scistag.webstag.server import WebStagService
    from scistag.vislog.renderers.log_renderer import LogRenderer
    from scistag.vislog.renderers.log_renderer_html import HtmlLogRenderer
    from scistag.vislog.visual_log_builder import LogBuilder
    from scistag.vislog.common import LogStatistics
    from scistag.vislog.options import LogOptions

# Error messages
TABLE_PIPE = "|"
"Defines the character which starts and ends an ASCII table in a log file"

_ONLY_AUTO_CLEAR_ON_CONTINUOUS = (
    "'auto_clear' can only be used in " "combination with 'continuous=True'"
)

_CONTINUOUS_NO_EFFECT_WITHOUT_BUILDER = (
    "continuous has no effect and should not be " "passed if builder is None"
)

_CONTINUOUS_REQUIRES_OVERWRITE = (
    "It does not make sense to run the "
    "log with continuous=True to update "
    "the log frequently if you forbid "
    "updating it."
)

_CONTINUOUS_REQUIRED_BG_THREAD = (
    "To update the log via this method "
    "you have to set 'mt' to True "
    "so the server can run in a "
    "background thread."
)

_ERROR_NO_APP_AUTO_RELOAD = (
    "Auto-reloading is not supported "
    "for apps as of now, please use "
    "a browser for testing and "
    "switch to app mode for "
    "deployment w/o autoreload."
)

_ERROR_INSTALL_CUTE = (
    "Please install PySide 6 to run "
    "VisualLog "
    "as stand-alone application. You can do "
    "so via install PySide6-components or "
    "by adding cutestag as extra to SciStag, "
    "e.g. "
    "pip install scistag[common,cutestag]"
)

LOG_EVENT_CACHE_NAME = "__logEvents"
"Name of the cache entry in which the log events are stored"

SLEEPING_TEXT_MESSAGE = "\nZzzzzzz - Press Ctrl-C to terminate\n"

CUTE_APP = "cute"
"Defines that the app shall be started in a Qt browser window"

MAIN_LOG = "mainLog"
"The name of the main log"

BuilderCallback = Callable[["LogBuilder"], None]
"""
Type definition for a function which can be passed to VisualLog's initializer
to be called once or continuously to update the log.
"""

BuilderTypes = Union[BuilderCallback, "LogBuilder", Type["LogBuilder"]]
"""
The supported builder callback types.
 
Either a function which can be called, a LogBuilder object provided by
the user or a class of a LogBuilder ancestor class of which we shall
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

    def __init__(
        self,
        title: str = "SciStag - VisualLog",
        app: Literal["cute"] | None = None,
        start_browser: bool = False,
        resolution: Size2D | None = None,
        ref_dir: str | None = None,
        tmp_dir: str | None = None,
        clear_target_dir: bool = False,
        continuous_write=False,
        refresh_time_s=0.25,
        formats_out: set[str] | None = None,
        embed_images: bool | None = None,
        filetype: str | tuple[str, int] = "png",
        max_fig_size: Size2DTypes | None = None,
        cache_dir: str | None = None,
        cache_version: int = 1,
        cache_name: str = "",
        auto_reload: bool | BuilderTypes = False,
        target_dir: str = "./logs",
        index_name: str = "index",
        log_to_disk=False,
        log_to_stdout=False,
        debug: bool = False,
        options: "LogOptions" | None = None,
    ):
        """
        :param target_dir: The output directory
        :param title: The log's name
        :param index_name: Defines the name of the log's index file. index by
            default.

            Extensions such as .html, .md and .txt will automatically
            be added.
        :param app: Defines if the log shall behave like an application.

            In the future you will be able to pass here a application class
            or instance. At the moment you can pass "cute" to open the app
            in a webkit built-in browser (requires the extra "cutestag") or
            an explicit installation of pyside6 (or above).
        :param start_browser: Defines if a browser shall be started when the
            log winds up a web server.
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
            to disk. False by default.
        :param log_to_stdout: Defines if the system shall automatically log to
            stdout via print as well. False by default.
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
        :param filetype: The default output image format to store images
            and figures with. "png" by default.

            You can also pass the image format and image quality in a tuple
            such as ("jpg", 60).

            Alternatively "jpg" or "bmp" can be used (to minimize the bandwidth
            or in the later case if you are the intranet w/ unlimited bandwidth
            and want to host it live at maximum performance).
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
        :param debug: If set to true additional debug logging will be enabled
        :param options: Defines the full set of options.

            Explicitly via parameter passed values will override the corresponding
            values in the options set.
        """
        from scistag.vislog.options import LogOptions

        self.options = LogOptions() if options is None else options.copy(deep=True)
        """
        Defines the log's configuration
        """
        if debug:
            self.options.debug.enable()
        self._general_lock = StagLock()
        """
        Access lock to handle the page's events
        """
        self.start_time = time.time()
        "The time stamp of when the log was creation"
        try:
            if clear_target_dir and log_to_disk:
                shutil.rmtree(target_dir)
        except FileNotFoundError:
            pass
        if formats_out is None:
            formats_out = {HTML}
        self.index_name = index_name
        """
        The index file's name
        """
        self._app = app
        "Defines the initial application to wind up with this log"
        self._resolution = resolution
        "Defines the desired initial resolution"
        self._start_browser = start_browser
        "Defines if a browser shall be started once a local server is wind up"
        self._cache: Cache | None = None
        """
        The log's data cache to store computation results between execution
        sessions
        """
        self.last_page_request = 0.0
        """Defines the timestamp when the page was requested for the last time
        via http.
        """
        self._title = title
        "The log's title"
        self.target_dir = os.path.abspath(target_dir)
        "The directory in which the logs shall be stored"
        # setup the cache
        do_auto_reload = (
            isinstance(auto_reload, bool) and auto_reload
        ) or auto_reload is not None
        self._setup_cache(do_auto_reload, cache_version, cache_dir, cache_name)
        self.ref_dir = FilePath.norm_path(
            self.target_dir + "/ref" if ref_dir is None else ref_dir
        )
        "The directory in which reference files for comparison shall be stored"
        self.tmp_path = FilePath.norm_path(
            self.target_dir + "/temp" if tmp_dir is None else tmp_dir
        )
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
        self._max_fig_size = max_fig_size
        """
        The maximum figure size
        """
        "Defines the preview's width and height"
        self.default_stat_update_frequency = 1.0
        "The update frequency of the stats in seconds"
        self.log_formats = formats_out
        "Defines if text shall be logged"
        self.log_formats.add(CONSOLE)
        """
        Contains the log data for each output type
        """
        self.continuous_write = continuous_write
        "If defined the output logs will be updated after every log"
        self.markdown_html = True
        "Defines if markdown shall support html embedding"
        self.log_txt_images = True
        "Defines if images shall also be logged to text files as ASCII"
        self.embed_images = (
            embed_images if embed_images is not None else MD not in formats_out
        )
        if isinstance(filetype, tuple):  # unpack tuple if required
            filetype, image_quality = filetype
        else:
            image_quality = 90
        "If defined images will be embedded directly into the HTML code"
        self.image_format = filetype
        "The default image type to use for storage"
        self.image_quality = image_quality
        "The image compression quality"
        self._consoles: list[Console] = []
        "Attached consoles to which the data shall be logged"
        from scistag.vislog.renderers.log_renderer_html import HtmlLogRenderer

        self._renderers: dict[str, "LogRenderer"] = {
            HTML: HtmlLogRenderer(title=self._title)
        }
        "The renderers for the single supported formats"
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
        self.log_to_stdout = log_to_stdout
        "Defines if all log messages shall also be send to stdout via print"
        if do_auto_reload:
            self._events = self.cache.get(LOG_EVENT_CACHE_NAME, default=[])
        self._invalid = False
        "Defines if this log was invalidated via :meth:`invalidate`"
        self._total_update_counter = 0
        "The total number of updates to this log"
        self._update_counter = 0
        # The amount of updates since the last statistics update
        self._last_statistic_update = time.time()
        "THe last time the _update rate was computed as time stamp"
        self._update_rate: float = 0
        # The last computed updated rate in updates per second
        from .visual_log_builder import LogBuilder

        self.default_page = PageSession(
            log=self,
            builder=None,
            log_formats=self.log_formats,
            index_name=index_name,
            target_dir=self.target_dir,
            continuous_write=self.continuous_write,
            log_to_stdout=self.log_to_stdout,
            log_to_disk=log_to_disk,
        )
        """Defines the initial default target page in which the page data ia stored"""
        self.pages = [self.default_page]
        """A list of all currently active pages"""
        self.default_builder: LogBuilder = LogBuilder(
            self, page_session=self.default_page
        )
        self.default_page.set_builder(self.default_builder)
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
        self._testing = False
        """
        Defines if the log is run in test mode and e.g. shall not spawn a
        real http server
        """
        self.urls = []
        "List of urls at which the main page of this log can be accessed"
        self.live_urls = []
        "List of live urls at which the main page of this log can be accessed"
        self._builder_handler: BuilderTypes | None = None
        "The builder being used"
        self._auto_clear: bool = False
        "Defines if the log shall be cleared for continuous logs"
        self._continuous_build: bool = False
        "Defines if the log shall be rebuilt continuously"
        self._auto_reload = auto_reload
        "Defines if auto-reloading is active"
        # execute auto-reloader if provided
        if not isinstance(auto_reload, bool) and auto_reload is not None:
            self.run_server(
                host_name="127.0.0.1",
                builder=auto_reload,
                auto_reload=True,
                auto_reload_stag_level=2,
            )

    def terminate(self):
        """
        Sets the termination state to true so that if the log was
        initialized with the flag `continuous=True` it can be terminated
        from within the logging function.
        """
        with self._general_lock:
            self._shall_terminate = True

    def add_static_file(self, filename: str, content: bytes):
        """
        Provides a file statically, e.g. to provide it via a
            VisualLiveLogServer.

        Multi-thread safe function.

        :param filename: The name of the data to add
        :param content: The file's content
        """
        with self._general_lock:
            self.static_files[filename] = content

    def get_file(self, filename: str) -> bytes | None:
        """
        Tries to receive a file created by this log, either stored locally
        or in memory via :meth:`add_static_file`.

        :param filename: The file's name
        :return: The file's content (if available)
        """
        with self._general_lock:
            if filename in self.static_files:
                return self.static_files[filename]
            abs_filename = os.path.abspath(self.target_dir + "/" + filename)
            if not abs_filename.startswith(self.target_dir):
                return None
            return FileStag.load(abs_filename)

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
        return Size2D(self._max_fig_size)

    def _provide_live_view(self):
        """
        Assembles a website file which automatically updates the
        logged html file as often as possible when ever it is updated
        on disk.
        """
        base_path = self._get_module_path()
        css = FileStag.load(base_path + "/css/visual_log.css")
        if self.log_to_disk:
            FileStag.save(f"{self.target_dir}/css/visual_log.css", css, create_dir=True)
        self.add_static_file("css/visual_log.css", css)
        import jinja2

        environment = jinja2.Environment()
        css = FileStag.load_text(FilePath.absolute_comb("css/visual_log.css"))
        properties = {
            "css": css,
            "title": self._title,
            "reload_timeout": 2000,
            "retry_frequency": 100,
            "reload_frequency": int(self.refresh_time_s * 1000),
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
        self.add_static_file("liveView.html", rendered_lv.encode("utf-8"))

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

    def flush(self):
        """
        Writes the current state to disk
        """
        self.default_page.write_to_disk()

    def finalize(self) -> VisualLog:
        """
        Finalizes the report and writes it to disk

        :return: The VisualLog object
        """
        self.default_page.write_to_disk(render=True)
        if FilePath.exists(self.tmp_path):
            shutil.rmtree(self.tmp_path)
        return self

    def create_web_service(
        self, support_flask: bool = False, url_prefix: str = ""
    ) -> "WebStagService":
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
        from scistag.vislog.server.visual_log_service import VisualLogService

        service = WebClassService(
            "VisualLogService", url_prefix=url_prefix, support_flask=support_flask
        )
        service.add_class(VisualLogService, service_name="", parameters={"log": self})
        return service

    def run_server(
        self,
        builder: BuilderTypes | None = None,
        host_name: str = "127.0.0.1",
        port: int | tuple[int, int] = 8010,
        url_prefix: str = "",
        public_ips: str | list[str] | None = None,
        continuous: bool | None = None,
        wait: bool = True,
        auto_clear: bool | None = None,
        mt: bool = True,
        test: bool = False,
        server_logs: bool = False,
        show_urls: bool = True,
        auto_reload=False,
        auto_reload_stag_level: 1 = 1,
        **kwargs,
    ):
        """
        Hosts the log as web service.

        This way you can either provide the log as a static website or
        even update it dynamically and

        :param builder: An (optional) function to be called to build or
            (repetitively) rebuild the log's content.

            The function can be called once - if continuous=False was passed,
            continuously with a frequency of :attr:`refresh_time_s`
            (as passed to the constructor) if continuous=True was passed.

            Instead of passing a builder callback you can as well as also
            just fill the log with content before running :meth:`run_server`.
        :param host_name: The IP(s) to listen at.

            - 127.0.0.1 = Local access only (default) as
              "there is no place like localhost".
            - "0.0.0.0" = Listen at all local network adapters
        :param port: The port ot listen at or a port range to select the
            first port within. 8010 by default. 0 for a random port.
        :param url_prefix: The url prefix at which the service shall be hosted.

            "" = At https://server
            "log/" = At https://server/log
        :param public_ips: If you run the service on a virtual machine in
            the cloud you can pass its public IPs to log the correct
            connection URls to the console.

            If you pass "auto" as ip the public IP will be auto-detected via
            ipify.
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
            - continuous - which is not supported yet.
            - ...
        :param auto_reload_stag_level: Defines which module shall be observed
            and reloaded upon modifications.

            By default it is the method of the calling module (1). If you need
            e.g. to track the caller's caller (2) increase this number
            accordingly.
        :param kwargs: Additional parameters which shall be passed to the
            WebStagServer upon creation.
        """
        test = self._testing or test
        self._testing = test
        if builder is not None:
            builder = self.prepare_builder(builder, self.default_page)
        self._auto_clear = auto_clear
        self._continuous_build = continuous
        self._builder_handler = builder
        self.start_time = time.time()
        if not isinstance(auto_reload, bool) or auto_reload:
            self._auto_reload = True
            from scistag.vislog.auto_reloader.visual_log_auto_reloader import (
                VisualLogAutoReloader,
            )

            if continuous:
                raise NotImplementedError(
                    "Continuous mode is not supported yet by auto-reload"
                )
            self._run_builder(builder)
            self.handle_page_events()
            VisualLogAutoReloader.start(
                log=self,
                host_name=host_name,
                port=port,
                public_ips=public_ips,
                url_prefix=url_prefix,
                _stack_level=auto_reload_stag_level + 1,
            )
            return
        from scistag.webstag.server import WebStagServer

        service = self.create_web_service(support_flask=True, url_prefix=url_prefix)
        server = WebStagServer(
            host_name=host_name,
            port=port,
            services=[service],
            silent=not server_logs,
            **kwargs,
        )
        port = server.port
        self._server = server
        if continuous is not None:
            if builder is None:
                raise ValueError(_CONTINUOUS_NO_EFFECT_WITHOUT_BUILDER)
            if not continuous:
                if auto_clear is not None and auto_clear:
                    raise ValueError(_ONLY_AUTO_CLEAR_ON_CONTINUOUS)
            else:
                if not mt:
                    raise ValueError(_CONTINUOUS_REQUIRED_BG_THREAD)
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
        self.urls = []
        self.live_urls = []
        protocol = "http://"
        if "localhost" not in public_ips and "127.0.0.1" not in public_ips:
            public_ips.append("127.0.0.1")
        for cur_ip in public_ips:
            if cur_ip == "0.0.0.0":
                continue
            self.urls.append(f"{protocol}{cur_ip}:{port}{url_prefix}")
            self.live_urls.append(f"{protocol}{cur_ip}:{port}{url_prefix}/live")
        if show_urls:
            print("\nVisualLog web service started\n")
            print("Connect at:")
            for cur_ip in public_ips:
                if cur_ip == "0.0.0.0":
                    continue
                print(f"* {protocol}{cur_ip}:{port}{url_prefix} for the static log")
                print(
                    f"* {protocol}{cur_ip}:{port}{url_prefix}/live for "
                    f"the auto-reloader"
                )
                print("\n")
        if not continuous and not mt:  # if the server will block execute
            # once here, otherwise after the server started
            if builder is not None:  # call once
                self._run_builder(builder)
                self.handle_page_events()
                self.default_page.write_to_disk()
        server.start(mt=mt and not test, test=test)
        self._start_app_or_browser(real_log=self, url=self.local_live_url)
        self._run_log_mt(mt, wait, test=test)

    def _run_log_mt(self, mt: bool, wait: bool, test: bool = False):
        """
        Runs the log updating when the log itself runs in the background

        :param mt: Defines if multi-threading is being used
        :param wait: Defines if the thread shall wait till the log is terminated
        :param test: Defines if the server runs in test mode
        """
        if self._continuous_build:
            auto_clear = self._auto_clear if self._auto_clear is not None else True
            self._run_continuous(auto_clear, self._builder_handler)
        elif mt:
            if self._builder_handler is not None:  # call once
                self._run_builder(self._builder_handler)
                self.handle_page_events()
                self.default_page.write_to_disk()
            if wait:
                self.sleep()

    def run(
        self,
        builder: BuilderTypes,
        continuous: bool | None = None,
        auto_clear: bool | None = None,
        overwrite: bool | None = None,
        auto_reload: bool = False,
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
            builder = self.prepare_builder(builder, self.default_page)
        self._auto_clear = auto_clear
        self._continuous_build = continuous
        self._builder_handler = builder
        self.start_time = time.time()
        if self.log_to_disk and HTML in self.log_formats:
            self.urls.append(
                "file://" + self.default_page.html_filename.replace("\\", "/")
            )
        if not isinstance(auto_reload, bool) or auto_reload:
            self._auto_reload = True
            from scistag.vislog.auto_reloader.visual_log_auto_reloader import (
                VisualLogAutoReloader,
            )

            if continuous:
                raise NotImplementedError(
                    "Continuous mode is not supported yet by auto-reload"
                )
            self._run_builder(builder)
            self.handle_page_events()
            VisualLogAutoReloader.start(log=self, host_name=None, _stack_level=2)
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
            self._run_builder(builder)
            self.handle_page_events()
            self.default_page.write_to_disk()
        if continuous:
            auto_clear = auto_clear if auto_clear is not None else True
            self._run_continuous(auto_clear, builder)
        if self.log_to_disk and HTML in self.log_formats:
            if self._start_browser:
                self._start_app_or_browser(self, url=self.default_page.html_filename)
                return True

    def _run_builder(self, builder: BuilderTypes | None = None):
        """
        Runs the associated builder

        :param builder: The builder to be called from rebuild the log
        """
        if builder is not None:
            if getattr(builder, "build", None) is not None:
                builder.build_page()
            else:
                builder(self.default_builder)
        self.default_page.write_to_disk()

    def prepare_builder(self, builder: BuilderTypes, page_session: PageSession):
        """
        Prepapres the builder to be used for this log

        :param builder: The build helper, either a function which fills the
            log or an ancestor of LogBuilder implementing at least the
            build_body method to do the same.
        :param page_session: Defines the target page to which the builder shall write
        :return: The prepared build object
        """
        if isinstance(builder, type):
            from .visual_log_builder import LogBuilder

            builder: Type[LogBuilder] | LogBuilder
            builder = builder(log=self, page_session=page_session)
            if not isinstance(builder, LogBuilder):
                raise TypeError("No valid LogBuilder base class provided")
        return builder

    def _start_app_or_browser(self, real_log: VisualLog, url: str):
        """
        This function is called when the log is set up and ready to go

        If an application setup was attached or a browser shall be started,
        this function does just start.

        :param real_log: Defines the log which actually hosts the web service
        :param url: Defines the URL which shall be opened
        """

        if self._start_browser:
            import webbrowser

            # check if an old browser is alive
            wait_time = max([real_log.refresh_time_s, 0.5])
            time.sleep(wait_time * 1.5)
            # if the page was loaded don't open another browser
            if time.time() - real_log.last_page_request > wait_time:
                webbrowser.open(url)
                return
        if self._app is not None and len(self._app) != 0:
            if self._app == CUTE_APP:
                from scistag.cutestag import cute_available

                if not cute_available():
                    raise AssertionError(_ERROR_INSTALL_CUTE)
                if self._auto_reload:
                    raise NotImplementedError(_ERROR_NO_APP_AUTO_RELOAD)
                from scistag.cutestag.browser import CuteBrowserApp

                app = CuteBrowserApp(initial_url=url)
                from scistag.vislog.common.background_handler import BackgroundHandler

                bg_handler = BackgroundHandler(self)
                bg_handler.start()
                if not self._testing:
                    app.run()
                    self.server.kill()  # kill flask
                self.terminate()  # kill self
                bg_handler.terminate()  # kill bg thread
                if self._testing:
                    return
                # pragma: no-cover
                if not self._testing:
                    exit(0)
            raise ValueError(f"Unknown application type: {self._app}")

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
        print(SLEEPING_TEXT_MESSAGE)
        while not self._shall_terminate:
            next_event = self.handle_page_events()
            max_sleep_time = self.refresh_time_s
            if next_event is not None:
                max_sleep_time = max(min(max_sleep_time, next_event - time.time()), 0)
            time.sleep(max_sleep_time)
            if self._testing:
                break

    def _run_continuous(self, auto_clear: bool, builder: BuilderCallback):
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
            with self._general_lock:
                if self._shall_terminate:
                    break
            if auto_clear:
                self.clear()
            self._run_builder(builder)
            self.handle_page_events()
            self.default_page.write_to_disk()
            cur_time = time.time()
            while cur_time < next_update:
                time.sleep(next_update - cur_time)
                cur_time = time.time()
            # try to keep the frequency but never build up debt:
            next_update = max(next_update + self.refresh_time_s, cur_time)
            self.update_statistics(cur_time)

    def handle_page_events(self) -> float | None:
        """
        Handles the events for all known pages

        :return: The timestamp at which we assume the next event to occur
        """
        next_event = None
        for page in self.pages:
            next_event_time = page.handle_events()
            if next_event_time is not None:
                if next_event is None or next_event_time < next_event:
                    next_event = next_event_time
        return next_event

    @property
    def server(self) -> "WebStagServer":
        """
        Returns the server (if one was created) and started via
        :meth:`run_server`.
        """
        return self._server

    @property
    def local_live_url(self) -> str | None:
        """
        Returns the local url at which the log can be displayed in a local
        browser.
        """
        if len(self.urls) == 0:
            return None
        return self.live_urls[0]

    @property
    def local_static_url(self) -> str | None:
        """
        Returns the local url at which the log can be displayed in a local
        browser.

        Returns the static page w/o dynamic updating support from server side.
        """
        if len(self.urls) == 0:
            return None
        return self.urls[0]

    @property
    def cache(self) -> Cache:
        """
        Returns the log's cache object to cache computation data between
        functions repetitions or even multiple execution sessions.
        """
        return self._cache

    def update_statistics(self, cur_time: float):
        """
        Updates the statistics if necessary

        :param cur_time: The current system time (in seconds)
        """
        # update once per second if fps is high, otherwise once all x seconds
        update_frequency = (
            self.default_stat_update_frequency
            if (self._update_rate == 0.0 or self._update_rate > 20)
            else 5.0
        )
        if cur_time - self._last_statistic_update > update_frequency:
            time_diff = cur_time - self._last_statistic_update
            self._update_rate = self._update_counter / time_diff
            self._last_statistic_update = cur_time
            self._update_counter = 0

    def _setup_cache(
        self,
        auto_reload: bool,
        cache_version: str | int,
        cache_dir: str,
        cache_name: str,
    ):
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
            cache_dir = f"{os.path.abspath(self.target_dir)}/.stscache/{cache_name}"
        else:
            cache_dir = f"{cache_dir}/{cache_name}"
        auto_reload_cache = None
        if auto_reload:  # if auto-reloading is enabled try to restore cache
            # check if there is a valid, prior cache available
            from scistag.vislog.auto_reloader.visual_log_auto_reloader import (
                VisualLogAutoReloader,
            )

            auto_reload_cache = VisualLogAutoReloader.get_cache_backup()
            if (
                auto_reload_cache is not None
                and auto_reload_cache.version != cache_version
            ):
                auto_reload_cache = None
        self._cache = (
            Cache(
                cache_dir=cache_dir,
                version=cache_version,
            )
            if auto_reload_cache is None
            else auto_reload_cache
        )

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

    def get_statistics(self) -> "LogStatistics":
        """
        Returns statistics about the log

        :return: A dictionary with statistics about the log such as
            - totalUpdateCount - How often was the log updated?
            - updatesPerSecond - How often was the log updated per second
            - upTime - How long is the log being updated?
        """

        from scistag.vislog.common.log_statistics import LogStatistics

        return LogStatistics(
            update_counter=self._total_update_counter,
            update_rate=self._update_rate,
            uptime=time.time() - self.start_time,
        )

    def clear(self):
        """
        Clears the default page log (excluding headers and footers)
        """
        self.default_page.clear()

    @classmethod
    def is_main(cls) -> bool:
        """
        Returns if the file calling this method was the main entry point
        before the module got reloaded.

        Only available if auto-reloading is being used.

        :return: True if the calling method is in the main module.
        """
        if StagApp.is_main(2):
            return True
        from scistag.vislog.auto_reloader.visual_log_auto_reloader import (
            VisualLogAutoReloader,
        )

        return VisualLogAutoReloader.is_main(2)

    @staticmethod
    def setup_micro_log(target_dir: str = "./"):
        """
        Creates a set of files in the defined directory which contain
        replacements for the essential logging classes such as VisualLog,
        LogBuilder etc. which can be used on systems without
        a valid SciStag installation such as MicroPython.

        ..  code-block:python

            try:
                from scistag.vislog import VisualLog, LogBuilder
                VisualLog.setup_mocks()
            except ModuleNotFoundError:
                from visual_log_mock import VisualLog, LogBuilder
        """
        from .visual_micro_log import VisualMicroLock

        VisualMicroLock.setup_micro_lock(target_dir)

    @property
    def is_micro(self) -> bool:
        """
        Returns if this builder is a minimalistic logger with limited
        functionality.

        See :meth:`setup_mocks`

        :return: True if it is a mock
        """
        return False

    def __enter__(self) -> "LogBuilder":
        """
        Returns the default builder

        ..  code-block:

            with VisualLog() as vl:
                vl.title("Hello world")

        :return: The builder object
        """
        return self.default_builder

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()

    __all__ = ["VisualLog", "LogStatistics", "HTML", "MD", "TXT", "TABLE_PIPE"]
