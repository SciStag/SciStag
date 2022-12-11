"""
Test the autoreload capabilities
"""
import os.path
import time
from threading import Thread

from scistag.vislog.auto_reloader.visual_log_auto_reloader import VisualLogAutoReloader


class AutoReloadTestThread(Thread):
    """
    Helper thread to kill the auto-reloader after a certain amount of time
    and trigger the reload behavior several times w/ and w/o errors
    """

    def __init__(self, duration, max_wait_time=2.0):
        """
        :param duration: The duration to wait until the auto-reloading shall
            be stopped
        :param max_wait_time: The maximum wait time for a fail in seconds,
            e.g. failed setup
        """
        super().__init__()
        self.duration = duration
        self.max_wait_time = max_wait_time
        self.failed = False

    def run(self) -> None:
        start_time = time.time()
        # just spend time
        while VisualLogAutoReloader.get_test_client() is None:
            time.sleep(0.1)
            if time.time() - start_time > self.max_wait_time:
                self.failed = True
                VisualLogAutoReloader.terminate()
                return
        # cause an error
        time.sleep(0.11)
        self.write_dummy_log("121332ThisIsCausingAnError")
        time.sleep(0.11)
        # create a healthy file again
        self.write_dummy_log("abc=123")
        while time.time() - start_time < self.duration:
            time.sleep(0.11)
        time.sleep(0.11)
        VisualLogAutoReloader.terminate()
        VisualLogAutoReloader.testing = False

    @staticmethod
    def write_dummy_log(add_content=""):
        rel_path = os.path.dirname(__file__)
        with open(f"{rel_path}/generic_module.py", "w") as text_file:
            text_file.write(
                f"""
from scistag.vislog import VisualLogBuilder, VisualLog
def builder(vl: VisualLogBuilder):
    vl.log("Hello testlog")
{add_content}    
log = VisualLog(auto_reload=builder)
        """
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
