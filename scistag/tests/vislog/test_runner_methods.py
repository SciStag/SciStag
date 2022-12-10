"""
Tests server and continuous execution
"""
import time
from threading import Thread
from unittest import mock

from scistag.vislog import VisualLog, VisualLogBuilder
from scistag.vislog.auto_reloader.visual_log_auto_reloader import \
    VisualLogAutoReloader


def test_log_runner_basics():
    """
    Tests the basic runner functionality
    """
    log = VisualLog()
    log.default_stat_update_frequency = 0.2
    log.update_statistics(time.time())
    time.sleep(0.25)
    log.update_statistics(time.time())
    statistics = log.get_statistics()
    assert statistics.update_rate >= 0
    assert not log.is_main()


class DummyBuilder(VisualLogBuilder):
    def build(self):
        self.log("Some content")
        if self.target_log.get_statistics().update_counter == 2:
            self.target_log.terminate()


def builder_callback(vl: VisualLogBuilder):
    vl.clear()
    vl.log("Some function content")
    vl.log(vl.target_log.max_fig_size)
    if vl.target_log.get_statistics().update_counter == 2:
        vl.target_log.terminate()


class AutoreloadKillThread(Thread):
    """
    Helper class to help test to get free of testing loop
    """

    def __init__(self, log: VisualLog, duration):
        super().__init__()
        self.log = log
        self.duration = duration

    def run(self) -> None:
        start_time = time.time()
        while True:
            time.sleep(0.01)
            if time.time() - start_time > self.duration:
                break
        VisualLogAutoReloader.terminate()


def test_builder_calls():
    """
    Tests the callbacks of different builder types with a simple run
l    """
    log = VisualLog()
    log.run(builder=DummyBuilder)
    assert b"Some content" in log.get_page("html")
    log = VisualLog()
    log.run(builder=builder_callback, overwrite=False)
    assert b"Some function content" in log.get_page("html")
    log = VisualLog(refresh_time_s=0.05)
    log.run(builder=DummyBuilder, continuous=True)
    assert b"Some content" in log.get_page("html")
    log = VisualLog(refresh_time_s=0.05)
    log.run(builder=builder_callback, continuous=True, auto_clear=True)
    assert b"Some function content" in log.get_page("html")
    VisualLogAutoReloader.testing = True
    with mock.patch('builtins.print'):
        log = VisualLog(refresh_time_s=0.05)
        kt = AutoreloadKillThread(log, duration=0.25)
        kt.start()
        # auto reload with class
        log.run(builder=DummyBuilder, auto_reload=True)

        log = VisualLog(refresh_time_s=0.05)
        kt = AutoreloadKillThread(log, duration=0.25)
        kt.start()
        # auto reload w/ method
        log.run(builder=builder_callback, auto_reload=True)


@mock.patch("builtins.print")
def test_run_server(pbi):
    """
    Tests running the log explicitly as server
    """
    log = VisualLog()
    log.run_server(builder=DummyBuilder, public_ips=["auto"], mt=True,
                   test=True)
    log = VisualLog()
    log.run_server(builder=DummyBuilder, public_ips=["auto"], mt=True,
                   test=True, continuous=True)
    log = VisualLog()
    log.run_server(builder=DummyBuilder, public_ips=["auto"], mt=False,
                   test=True, continuous=False)
