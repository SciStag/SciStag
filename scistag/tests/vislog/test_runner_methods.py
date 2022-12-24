"""
Tests server and continuous execution
"""
import time
from threading import Thread
from unittest import mock

import pytest

from scistag.common.time import sleep_min
from scistag.vislog import VisualLog, VisualLogBuilder
from scistag.vislog.auto_reloader.visual_log_auto_reloader import VisualLogAutoReloader


def test_log_runner_basics():
    """
    Tests the basic runner functionality
    """
    log = VisualLog()
    log.default_stat_update_frequency = 0.2
    log.update_statistics(time.time())
    sleep_min(0.25)
    log.update_statistics(time.time())
    statistics = log.get_statistics()
    assert statistics.update_rate >= 0
    assert not log.is_main()
    with mock.patch("scistag.common.stag_app.StagApp.is_main", lambda val: True):
        assert log.is_main()


class DummyBuilder(VisualLogBuilder):
    def build(self):
        self.add("Some content")
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


class DummyClassWithCorrectInit:
    def __init__(self, *args, **kwargs):
        pass


def test_builder_calls():
    """
        Tests the callbacks of different builder types with a simple run
    l"""
    with pytest.raises(TypeError):
        log = VisualLog()
        log.prepare_builder(builder=VisualLog, page_session=log.default_page)
    with pytest.raises(TypeError):
        log = VisualLog()
        log.prepare_builder(
            builder=DummyClassWithCorrectInit, page_session=log.default_page
        )
    log = VisualLog()
    log.run(builder=DummyBuilder)
    assert b"Some content" in log.default_page.get_page("html")
    log = VisualLog()
    log.run(builder=builder_callback, overwrite=False)
    assert b"Some function content" in log.default_page.get_page("html")
    log = VisualLog(refresh_time_s=0.05)
    log.run(builder=DummyBuilder, continuous=True)
    assert b"Some content" in log.default_page.get_page("html")
    log = VisualLog(refresh_time_s=0.05)
    log.run(builder=builder_callback, continuous=True, auto_clear=True)
    assert b"Some function content" in log.default_page.get_page("html")
    VisualLogAutoReloader.testing = True
    with mock.patch("builtins.print"):
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
        with pytest.raises(AssertionError):
            log.kill_server()
    with pytest.raises(ValueError):
        log = VisualLog()
        log.run(builder=None)
    with pytest.raises(ValueError):
        log = VisualLog()
        log.run(builder=DummyBuilder, continuous=False, auto_clear=True)
    with pytest.raises(ValueError):
        log = VisualLog()
        log.run(builder=DummyBuilder, continuous=True, overwrite=False)
    log = VisualLog(start_browser=True, log_to_disk=True)
    with mock.patch.object(log, "_start_app_or_browser", lambda self, url: None):
        log.run(builder=DummyBuilder)


@mock.patch("builtins.print")
def test_run_server(pbi):
    """
    Tests running the log explicitly as server
    """
    log = VisualLog()
    log.run_server(
        host_name="0.0.0.0",
        builder=DummyBuilder,
        public_ips=["auto", "0.0.0.0"],
        mt=True,
        test=True,
    )
    with pytest.raises(ValueError):
        log = VisualLog()
        log.run_server(
            builder=None,
            mt=True,
            test=True,
            continuous=True,
        )
    with pytest.raises(ValueError):
        log = VisualLog()
        log.run_server(
            builder=DummyBuilder,
            mt=True,
            test=True,
            auto_clear=True,
            continuous=False,
        )
    with pytest.raises(ValueError):
        log = VisualLog()
        log.run_server(builder=DummyBuilder, mt=False, test=True, continuous=True)

    log = VisualLog()
    log.run_server(
        builder=DummyBuilder, public_ips=["auto"], mt=True, test=True, continuous=True
    )
    log = VisualLog()
    log.run_server(
        builder=DummyBuilder, public_ips=["auto"], mt=False, test=True, continuous=False
    )
    log = VisualLog()
    log.run_server(
        builder=DummyBuilder, public_ips="auto", mt=False, test=True, continuous=False
    )
    log = VisualLog()
    log.run_server(
        host_name="0.0.0.0", builder=DummyBuilder, mt=True, test=True, continuous=False
    )
    log.kill_server()
