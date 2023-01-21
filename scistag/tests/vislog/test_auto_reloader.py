"""
Test the autoreload capabilities
"""
import os.path
import time
from threading import Thread

from scistag.common.time import sleep_min
from scistag.vislog.auto_reloader.visual_log_auto_reloader import VisualLogAutoReloader


class AutoReloadTestThread(Thread):
    """
    Helper thread to kill the auto-reloader after a certain amount of time
    and trigger the reload behavior several times w/ and w/o errors
    """

    def __init__(self, duration, max_wait_time=2.0, as_server: bool = False):
        """
        :param duration: The duration to wait until the auto-reloading shall
            be stopped
        :param max_wait_time: The maximum wait time for a fail in seconds,
            e.g. failed setup
        :param as_server: Defines if the service shall be started as a server
        """
        super().__init__()
        self.duration = duration
        self.max_wait_time = max_wait_time
        self.failed = False
        self.as_server = as_server

    def run(self) -> None:
        start_time = time.time()
        # just spend time
        while VisualLogAutoReloader.get_test_client() is None:
            sleep_min(0.01)
            if time.time() - start_time > self.max_wait_time:
                self.failed = True
                VisualLogAutoReloader.terminate()
                return
        # cause an error
        sleep_min(0.11)
        self.write_dummy_log("121332ThisIsCausingAnError", server=self.as_server)
        sleep_min(0.11)
        # create a healthy file again
        self.write_dummy_log("abc=123", server=self.as_server)
        while time.time() - start_time < self.duration:
            sleep_min(0.11)
        sleep_min(0.11)
        start_time = time.time()
        while time.time() - start_time < self.duration:
            sleep_min(0.11)
        sleep_min(0.11)
        VisualLogAutoReloader.terminate()
        VisualLogAutoReloader.testing = False

    @staticmethod
    def write_dummy_log(add_content="", server=False):
        rel_path = os.path.dirname(__file__)
        fn = (
            f"{rel_path}/generic_module.py"
            if not server
            else f"{rel_path}/generic_module_server.py"
        )
        with open(fn, "w") as text_file:
            text_file.write(
                f"""
from scistag.vislog import LogBuilder, VisualLog
def builder(vl: LogBuilder):
    vl.log("Hello testlog")
options = VisualLog.setup_options()
{add_content}    
        """
            )
            if not server:
                text_file.write(
                    """
log = VisualLog(options=options).run(builder, auto_reload=True)"""
                )
            else:
                text_file.write(
                    """
log = VisualLog(options=options).run_server(builder, auto_reload=True)"""
                )


def test_auto_reload():
    """
    Tests auto-reloading capabilities
    """

    VisualLogAutoReloader.testing = True
    kill_thread = AutoReloadTestThread(duration=0.0)
    AutoReloadTestThread.write_dummy_log()
    kill_thread.start()
    from unittest.mock import patch

    with patch("builtins.print") as print_patch:
        from .generic_module import builder

        test_client = VisualLogAutoReloader.get_test_client()
        assert test_client is not None
        content = test_client.get("/index")
        assert content.text is not None
        assert "testlog" in content.text
        assert VisualLogAutoReloader.reload_count >= 2
        assert VisualLogAutoReloader.error_count >= 1
    VisualLogAutoReloader.testing = False
    VisualLogAutoReloader.reset()
    assert VisualLogAutoReloader.error_count == 0
    assert VisualLogAutoReloader.reload_count == 0
    assert not kill_thread.failed


def test_auto_reload_server():
    """
    Tests auto-reloading capabilities
    """

    VisualLogAutoReloader.reset()
    VisualLogAutoReloader.testing = True
    kill_thread = AutoReloadTestThread(duration=0.0, as_server=True)
    add_content = """
from scistag.vislog.auto_reloader.visual_log_auto_reloader import ( 
VisualLogAutoReloader,
) 
auto_reload_cache = VisualLogAutoReloader.get_cache_backup()
if auto_reload_cache is not None:
    auto_reload_cache.version = 3
options.cache.version=2"""
    AutoReloadTestThread.write_dummy_log(add_content, server=True)
    kill_thread.start()
    from unittest.mock import patch

    with patch("builtins.print") as print_patch:
        from .generic_module_server import builder
    VisualLogAutoReloader._run_loop()
    VisualLogAutoReloader.testing = False
    VisualLogAutoReloader.reset()
