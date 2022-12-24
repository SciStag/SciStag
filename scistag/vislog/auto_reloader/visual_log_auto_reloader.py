"""
Implements the class :class:`VisualLogAutoReloader` which allows the live
editing of logs with the content changes being asap reflected in your IDE
and/or browser window.

It hosts a VisualLog as server at a defined IP as webservice and continuously
scans one or more source files for changes who create a log by themselves.
When ever any file was changed it lets these files build their log anew,
embeds its content and provides on a website.
"""

from __future__ import annotations

import inspect
import os.path
import sys
import time
from importlib import reload
from typing import Union, TYPE_CHECKING

from scistag.common import StagLock
from scistag.filestag import FileStag
from scistag.vislog import VisualLog

if TYPE_CHECKING:
    from scistag.common.cache import Cache

ERROR_TEXT = (
    "Yikes! An error occurred 🙍 - Please fix the bug 🐛 above and "
    "save the file to continue"
)
"Error text to be shown when the module stopped working"
HEALTHY_AGAIN_TEXT = "Yay - the module is healthy again, let's rock on! 🤘👨"
"Text to be shown when healthy again"


class VisualLogAutoReloader:
    _access_lock = StagLock()
    """
    Multithreading access lock
    """
    main_log: VisualLog | None = None
    """
    The main log which is staying alive during the restart sessions and is
    connected to the http server to host it's content.
    """
    _initial_filename: str = ""
    "The name of the source file which initially started the reload process"
    _embedded_log: VisualLog | None = None
    """
    The log which shall get embedded. (the actual content).
    
    This log will be re-created each modification turn.
    """
    _reloading: bool = False
    "Defines if the log is currently reloading"
    _cache_backup: Union["Cache", None] = None
    "A backup of the log's cache from the last execution session"
    content = None
    "The last file content state"
    imp_module = None
    "The name of the module we need to reimport"
    was_sick: bool = False
    "Flag if the last time there was an error which stopped the reloading"
    testing: bool = False
    "Defines if the server shall be started in test_mode"
    _test_client = None
    "The server test client (if started in testing mode)"
    _shall_terminate = False
    """
    Defines if the auto-reloader shall terminate and quit its infinite loop
    """
    reload_count = 0
    "The count how often the modules were reloaded since start"
    error_count = 0
    "The count of often the file count not be reloaded due to errors"

    @classmethod
    def setup(cls, refresh_time_s: float = 0.1, **params):
        """
        Setups the envelope VisualLog into which the live updating one will
        get embedded.

        :param refresh_time_s: The (maximum) refresh time in seconds and thus
            also about the delay between saving the file and seeing the
            result on screen.

            The browser will not replace/refresh the page if the value is quite
            low as the update script will detect there were no changes.
        :param params: Additional creation parameters. See :class:`VisualLog`.
        """
        log_to_disk = params.pop("log_to_disk", False)
        cls.main_log = VisualLog(
            title=cls._embedded_log._title,
            log_to_disk=log_to_disk,
            refresh_time_s=refresh_time_s,
        )

    @classmethod
    def set_log(cls, log):
        """
        The current log. As there log will get recreated each turn this
        object will change when ever the user's log gets updated.

        :param log: The new log of the current run
        """
        cls._embedded_log = log

    @classmethod
    def update_content(cls):
        """
        Updates the log's content by rendering first the embedded log
        and then the main (server) log which embeds it.
        """
        if cls.main_log is None or cls._embedded_log is None:
            return
        cls._embedded_log.default_page.render()
        cls.main_log.clear()
        cls.main_log.default_page.embed(cls._embedded_log.default_page)
        cls.main_log.default_page.render()

    @classmethod
    def is_main(cls, _stack_level=1) -> bool:
        """
        Returns if the file from which you call this method was originally
        the __main__ module when the AutoReloader was initialized.

        .. code-block:

           if __name__ == "__main__" or VisualLogAutoReloader.is_main():
                ...
        :param _stack_level: Defines if the stack depth at which the call
            origin shall be verified. By default the calling function (1).
        :return: True if the function from which this method was called
            was once the "__main__" module.
        """
        return cls._initial_filename == inspect.stack()[_stack_level].filename

    @classmethod
    def start(
        cls,
        log: VisualLog,
        host_name: str | None = "127.0.0.1",
        port: int | tuple[int, int] = 8010,
        public_ips: str | list[str] | None = None,
        url_prefix: str = "",
        check_time_s: float | None = None,
        server_params: dict | None = None,
        _stack_level=1,
    ):
        """
        Starts the auto-reloading service

        :param log:  The (initial) log which shall be provided by the service

            The log which shall be visualized in the live view. Due to the
            restarting/module reloading approach this log will be re-created
            each start and thus the object updated.
        :param host_name: The host name at which the log shall be hosted.

            Localhost by default.

            If None is passed no server will be started and no interaction
            is possible except via the console.
        :param port: The port ot listen at or a port range to select the
            first port within. 8010 by default. 0 for a random port.
        :param public_ips: If you run the service on a virtual machine in
            the cloud you can pass its public IPs to log the correct
            connection URls to the console.

            If you pass "auto" as ip the public IP will be auto-detected via
            ipify.
        :param url_prefix: The url prefix at which the service shall be hosted.

            "" = At http://server
            "log/" = At http://server/log
        :param server_params: Additional server parameters to be passed into
            :meth:`VisualLivelog.run_server` server main loop.
        :param check_time_s: The time interval at which files are checked
            for modification.
        :param _stack_level: The (relative) stack level of the file which
            shall be auto_reloaded.
        """
        VisualLogAutoReloader.set_log(log)
        if server_params is None:
            server_params = dict()
        if check_time_s is None:
            check_time_s = 0.05
        host_name = server_params.pop("host_name", host_name)
        if cls._reloading:
            return
        cls._reloading = True
        cls._initial_filename = inspect.stack()[_stack_level].filename
        cls.content = FileStag.load(cls._initial_filename)
        short_name = os.path.splitext(os.path.basename(cls._initial_filename))[0]
        import importlib.util

        spec = importlib.util.spec_from_file_location(short_name, cls._initial_filename)
        cls.imp_module = importlib.util.module_from_spec(spec)
        sys.modules[short_name] = cls.imp_module

        # Setup and run the server which will then host our (live) log's
        # content and stay alive during the restarts.
        cls.setup()
        cls.update_content()
        mt = server_params.pop("mt", True)
        if host_name is not None:
            cls.main_log._testing = cls.testing
            cls.main_log.run_server(
                host_name=host_name,
                port=port,
                public_ips=public_ips,
                url_prefix=url_prefix,
                mt=mt,
                **server_params,
            )
            with cls._access_lock:
                if cls.testing:  # return test client when in testing mode
                    cls._test_client = cls.main_log.server.handle.test_client()
                else:
                    cls._test_client = None
        try:
            print(f"Auto-reloading enabled for module {cls.imp_module}")
            cls._embedded_log._start_app_or_browser(
                real_log=cls.main_log, url=cls.main_log.local_live_url
            )
            while True:
                with cls._access_lock:
                    sht = cls._shall_terminate
                    if sht:
                        break
                time.sleep(check_time_s)
                cls._run_loop()
            with cls._access_lock:
                cls._shall_terminate = False
        except KeyboardInterrupt:
            if cls.main_log.server.server_thread is not None:
                cls.main_log.kill_server()
            return False
        return True

    @classmethod
    def terminate(cls):
        """
        Informs the auto-reloader that it shall quit its autoreload loop
        """
        with cls._access_lock:
            cls._shall_terminate = True

    @classmethod
    def reset(cls):
        """
        Resets the auto-reloader to it's base settings to provide a clean
        setup for testing it.
        """
        with cls._access_lock:
            cls._cache_backup = None
            cls._embedded_log = None
            del cls.main_log
            cls.main_log = None
            cls.content = None
            cls.was_sick = False
            cls.imp_module = None
            cls._test_client = None
            cls._initial_filename = ""
            cls.reload_count = 0
            cls.error_count = 0

    @classmethod
    def get_test_client(cls):
        """
        Returns the Flask/FastAPI test client if started in test mode
        :return: The test client
        """
        with cls._access_lock:
            return cls._test_client

    @classmethod
    def _run_loop(cls):
        """
        Handles the main loop which verifies if any element was modified
        and reloads all modified modules if required.
        """
        if cls._embedded_log is not None:
            widgets = cls.main_log.default_builder.widget
            events = widgets.get_events(clear=True)
            for event in events:
                cls._embedded_log.default_builder.widget.add_event(event)
        new_content = FileStag.load(cls._initial_filename)
        if new_content is None:
            new_content = b""
        try:
            cls._embedded_log.default_builder.widget.handle_event_list()
            if cls.content == new_content and not cls._embedded_log.invalid:
                return
            cls.content = new_content
            cls._reloading = True
            cls._cache_backup = cls._embedded_log.cache
            loop_start_time = time.time()
            with cls._access_lock:
                cls.reload_count += 1
            reload(cls.imp_module)
            rl_time = time.time() - loop_start_time
            VisualLogAutoReloader.update_content()
            if cls.was_sick:
                print(f"\u001b[32m\n{HEALTHY_AGAIN_TEXT} \u001b[0m")
                cls.was_sick = False
            else:
                print(f"... reloaded module in {rl_time:0.3f}s")
        except Exception as e:
            with cls._access_lock:
                cls.error_count += 1
            cls.was_sick = True
            print("\u001b[31m", end="")
            import traceback

            print(traceback.format_exc())
            print(f"\n{ERROR_TEXT}")
            print("\u001b[0m", end="")
            if isinstance(e, KeyboardInterrupt):
                raise KeyboardInterrupt
        cls._reloading = False

    @classmethod
    def get_cache_backup(cls) -> Union["Cache", None]:
        """
        Shall return the last VisualLog's cache data from the previous
        execution session.

        :return: The cache object if one was "rescued", otherwise None
        """
        return cls._cache_backup
