from __future__ import annotations
import inspect
import os.path
import sys
import time
from importlib import reload

from scistag.filestag import FileStag
from scistag.logstag import VisualLog


class VisualLogAutoReloader:
    log_server: VisualLog | None = None
    initial_filename: str = ""
    embedded_log: VisualLog | None = None
    reloading: bool = False

    @classmethod
    def setup(cls):
        cls.log_server = VisualLog(log_to_disk=False,
                                   refresh_time_s=0.1)

    @classmethod
    def set_log(cls, log):
        cls.embedded_log = log

    @classmethod
    def update_content(cls):
        if cls.log_server is None or cls.embedded_log is None:
            return
        cls.embedded_log.render()
        cls.log_server.clear_logs()
        cls.log_server.embed(cls.embedded_log)
        cls.log_server.render()

    @classmethod
    def is_main(cls, _stack_level=1) -> bool:
        return cls.initial_filename == inspect.stack()[_stack_level].filename

    @classmethod
    def start(cls, log: VisualLog, host: str = "127.0.0.1", _stack_level=1):
        VisualLogAutoReloader.set_log(log)
        if cls.reloading:
            return
        cls.reloading = True
        cls.initial_filename = inspect.stack()[_stack_level].filename
        content = FileStag.load_file(cls.initial_filename)
        short_name = os.path.splitext(os.path.basename(cls.initial_filename))[0]
        import importlib.util
        spec = importlib.util.spec_from_file_location(short_name,
                                                      cls.initial_filename)
        imp_module = importlib.util.module_from_spec(spec)
        sys.modules[short_name] = imp_module

        cls.setup()
        cls.update_content()
        cls.log_server.run_server(host, threaded=True)

        while True:
            time.sleep(0.1)
            new_content = FileStag.load_file(cls.initial_filename)
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
                print("E", end="")
                if isinstance(e, KeyboardInterrupt):
                    exit()
                print(e)
            cls.reloading = False
