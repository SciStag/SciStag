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

import ctypes
import inspect
import os.path
import sys
import time
from importlib import reload

from scistag.filestag import FileStag
from scistag.logstag import VisualLog


class VisualLogAutoReloader:
    log_server: VisualLog | None = None
    """
    The main log which is staying alive during the restart sessions and is
    connected to the http server to host it's content.
    """
    initial_filename: str = ""
    "The name of the source file which initially started the reload process"
    embedded_log: VisualLog | None = None
    """
    The log which shall get embedded. (the actual content).
    
    This log will be re-created each modification turn.
    """
    reloading: bool = False
    "Defines if the log is currently reloading"

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
        cls.log_server = VisualLog(log_to_disk=log_to_disk,
                                   refresh_time_s=refresh_time_s)

    @classmethod
    def set_log(cls, log):
        """
        The current log. As there log will get recreated each turn this
        object will change when ever the user's log gets updated.

        :param log: The new log of the current run
        """
        cls.embedded_log = log

    @classmethod
    def update_content(cls):
        """
        Updates the log's content by rendering first the embedded log
        and then the main (server) log which embeds it.
        """
        if cls.log_server is None or cls.embedded_log is None:
            return
        cls.embedded_log.render()
        cls.log_server.clear_logs()
        cls.log_server.embed(cls.embedded_log)
        cls.log_server.render()

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
        return cls.initial_filename == inspect.stack()[_stack_level].filename

    @classmethod
    def start(cls,
              log: VisualLog,
              host_name: str = "127.0.0.1",
              check_time_s: float | None = None,
              server_params: dict | None = None,
              _stack_level=1):
        """
        Starts the auto-reloading service

        :param log:  The (initial) log which shall be provided by the service

            The log which shall be visualized in the live view. Due to the
            restarting/module reloading approach this log will be re-created
            each start and thus the object updated.
        :param host_name: The host name at which the log shall be hosted.

            Localhost by default.
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
        if cls.reloading:
            return
        cls.reloading = True
        cls.initial_filename = inspect.stack()[_stack_level].filename
        content = FileStag.load(cls.initial_filename)
        short_name = os.path.splitext(os.path.basename(cls.initial_filename))[0]
        import importlib.util
        spec = importlib.util.spec_from_file_location(short_name,
                                                      cls.initial_filename)
        imp_module = importlib.util.module_from_spec(spec)
        sys.modules[short_name] = imp_module

        # Setup and run the server which will then host our (live) log's
        # content and stay alive during the restarts.
        cls.setup()
        cls.update_content()
        threaded = server_params.pop("threaded", True)
        cls.log_server.run_server(host_name, threaded=threaded,
                                  **server_params)

        try:
            while True:
                time.sleep(check_time_s)
                new_content = FileStag.load(cls.initial_filename)
                if new_content is None:
                    new_content = b""
                if content == new_content:
                    continue
                content = new_content
                cls.reloading = True
                try:
                    reload(imp_module)
                    VisualLogAutoReloader.update_content()
                    print(".", end="")
                except Exception as e:
                    print(f"An error occurred: {str(e)}")
                    if isinstance(e, KeyboardInterrupt):
                        raise KeyboardInterrupt
                cls.reloading = False
        except KeyboardInterrupt:
            if cls.log_server.server.server_thread is not None:
                cls.log_server.server.server_thread.kill()

