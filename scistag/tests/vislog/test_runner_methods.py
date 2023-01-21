"""
Tests server and continuous execution
"""
import time
from threading import Thread
from unittest import mock

import pytest

from scistag.common.time import sleep_min
from scistag.vislog import VisualLog, LogBuilder
from scistag.vislog.auto_reloader.visual_log_auto_reloader import VisualLogAutoReloader


def test_log_runner_basics():
    """
    Tests the basic runner functionality
    """
    log = VisualLog()
    assert not log.is_main()
    with mock.patch("scistag.common.stag_app.StagApp.is_main", lambda val: True):
        assert log.is_main()


class DummyBuilder(LogBuilder):
    def build(self):
        self.add("Some content")
        if self.stats.build_counter == 2:
            self.terminate()


def builder_callback(vl: LogBuilder):
    vl.clear()
    vl.log("Some function content")
    vl.log(vl.max_fig_size)
    if vl.stats.build_counter == 2:
        vl.terminate()


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
    options = VisualLog.setup_options()
    options.run.refresh_time_s = 0.05
    log = VisualLog(options=options)
    log.run(builder=DummyBuilder, continuous=True)
    assert b"Some content" in log.default_page.get_page("html")
    log = VisualLog(options=options)
    log.run(builder=builder_callback, continuous=True, auto_clear=True)
    assert b"Some function content" in log.default_page.get_page("html")
    VisualLogAutoReloader.testing = True
    with mock.patch("builtins.print"):
        log = VisualLog(options=options)
        kt = AutoreloadKillThread(log, duration=0.25)
        kt.start()
        # auto reload with class
        log.run(builder=DummyBuilder, auto_reload=True)

        log = VisualLog(options=options)
        kt = AutoreloadKillThread(log, duration=0.25)
        kt.start()
        # auto reload w/ method
        log.run(builder=builder_callback, auto_reload=True)
        with pytest.raises(AssertionError):
            log.kill_server()
    with pytest.raises(ValueError):
        options = VisualLog.setup_options()
        options.run.auto_clear = True
        options.run.continuous = False
        log = VisualLog(options=options)
        log.run(builder=DummyBuilder)
    options = VisualLog.setup_options()
    options.run.setup(app_mode="browser")
    log = VisualLog(options=options)
    with mock.patch.object(log, "_start_app_or_browser", lambda self, url: None):
        log.run(builder=DummyBuilder)
    options = VisualLog.setup_options("disk")
    options.run.setup(app_mode="browser")
    log = VisualLog(options=options)
    with mock.patch.object(log, "_start_app_or_browser", lambda self, url: None):
        log.run(builder=DummyBuilder)


@mock.patch("builtins.print")
def test_run_server(pbi):
    """
    Tests running the log explicitly as server
    """
    # 0.0.0.0 in public IPs
    options = VisualLog.setup_options("server")
    options.server.public_ips.append("0.0.0.0")
    log = VisualLog(options=options)
    log.run_server(builder=DummyBuilder, test=True)
    # string public IP
    options = VisualLog.setup_options("server")
    options.server.public_ips = "auto"
    log = VisualLog(options=options)
    log.run_server(builder=DummyBuilder, test=True)
    # none public IPs
    options = VisualLog.setup_options("server")
    options.server.public_ips = None
    log = VisualLog(options=options)
    log.run_server(builder=DummyBuilder, test=True)
    # single run
    options = VisualLog.setup_options("server")
    options.run.mt = False
    log = VisualLog(options=options)
    log.run_server(builder=DummyBuilder, test=True)
    with pytest.raises(ValueError):
        options = VisualLog.setup_options("server")
        options.run.continuous = True
        log = VisualLog(options=options)
        log.run_server(builder=None, test=True)
    with pytest.raises(ValueError):
        options = VisualLog.setup_options("local")
        options.run.mt = True
        options.run.continuous = False
        options.run.auto_clear = True
        log = VisualLog(options=options)
        log.run_server(
            builder=DummyBuilder,
            mt=True,
            test=True,
            auto_clear=True,
            continuous=False,
        )
    with pytest.raises(ValueError):
        options = VisualLog.setup_options("local")
        options.run.mt = False
        options.run.continuous = True
        log = VisualLog(options=options)
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
