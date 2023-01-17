"""
Advance LogBuilder tests
"""
import io
from contextlib import redirect_stdout

import pytest
from pydantic import BaseModel

from scistag.vislog import VisualLog, LogBuilder, cell


def test_creation():
    """
    Creation tests
    """
    base_log = VisualLog()
    new_builder = LogBuilder(log=base_log)
    assert new_builder.page_session is not None
    with pytest.raises(ValueError):
        base_log.default_builder.add(b"123")


def test_backup():
    """
    Tests creating and restoring a backup
    """
    log_a = VisualLog()
    log_a.default_builder.log("Test")
    log_b = VisualLog()
    log_b.default_builder.insert_backup(log_a.default_builder.create_backup())
    assert b"Test" in log_b.default_builder.create_backup().data["html"]


def test_static_file():
    """
    Tests adding static files
    """
    log_a = VisualLog()
    builder = log_a.default_builder
    builder.service.publish("testFile.bin", b"Hello world")
    assert builder.service.get_file("testFile.bin").body == b"Hello world"


global_called = False
global_main_called = False


@cell
def global_cell(lb: LogBuilder):
    global global_called
    global_called = True


def main(vl):
    global global_main_called
    global_main_called = True


def test_basic_building():
    """
    Tests the basic usage of cells and running the build process
    :return:
    """
    local_called = False

    class MyParams(BaseModel):
        some_value: int = 123

    class LB(LogBuilder):
        params_class = MyParams

        @cell
        def build_in(self):
            nonlocal local_called
            local_called = True

    log = VisualLog()
    log_a = log.run(LB, params={"some_value": 456})
    assert isinstance(log_a.params, MyParams)
    assert log_a.params.some_value == 456

    options = VisualLog.setup_options()
    result = LB.run(params={"some_value": 456})
    assert isinstance(result, dict)
    result = LB.run(params={"some_value": 456}, filetype="html", options=options)
    assert isinstance(result, bytes)
    assert global_called
    assert global_main_called
    assert local_called


def test_std_out():
    """
    Tests if logging to stdout is caught working
    :return:
    """
    std_out = io.StringIO()
    with redirect_stdout(std_out):
        options = VisualLog.setup_options("console")
        log = VisualLog(options=options)
        with log as lb:
            lb.log("Hello world")
        assert lb.get_result() == {}
    with redirect_stdout(std_out):
        options = VisualLog.setup_options("console")
        log = VisualLog(options=options)
        log.run(LogBuilder, nested=True)
        with log as lb:
            lb.log("Hello world")
        assert lb.nested
        assert lb.get_result() == {}
    assert "Hello world" in std_out.getvalue()


def test_current():
    """
    Tests the current method
    """

    class Builder(LogBuilder):
        @cell
        def content(self):
            assert LogBuilder.current() == self
            self.terminate()
            assert self.terminated

    Builder.run()
