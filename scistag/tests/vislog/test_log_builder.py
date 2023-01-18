"""
Advance LogBuilder tests
"""
from . import vl
import io
from contextlib import redirect_stdout

import pytest
from pydantic import BaseModel

from scistag.vislog import VisualLog, LogBuilder, cell, LogBackup
from ...filestag import FileStag


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
    options_a = VisualLog.setup_options()
    options_a.output.setup(formats={"txt", "html"})
    log_a = VisualLog(options=options_a)
    log_a.default_builder.log("Test")
    log_b = VisualLog()
    log_b.default_builder.insert_backup(log_a.default_builder.create_backup())
    log_c = VisualLog(options=options_a)
    log_c.default_builder.insert_backup(log_a.default_builder.create_backup())
    assert b"Test" in log_b.default_builder.create_backup().data["html"]


def test_backup_adv(tmp_path):
    """
    Tests the log's backup functionality
    """
    details = {}

    class MyBuilder(LogBuilder):
        @cell
        def hello(self):
            self.text("hello")

    MyBuilder.run(out_details=details)
    builder: LogBuilder = details["builder"]
    backup: LogBackup = builder.create_backup()
    assert b"hello" in backup.data["html"]

    backup.save_to_disk(str(tmp_path))
    assert b"hello" in FileStag.load(str(tmp_path) + "/index.html")


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


def test_advanced_br():
    """
    Tests the linebreak method
    """
    vl.test.checkpoint("lb.br")
    vl.br(1)
    vl.text("test")
    vl.br(3)
    vl.text("test after 3 line spacing")
    vl.br(1, exclude="html")
    vl.text("test after 1 line spacing, not in html")
    vl.br(1, exclude={"txt"})
    vl.text("test after 1 line spacing, not in txt")
    vl.br(1, exclude="md")
    vl.text("test after 1 line spacing, not in md")
    vl.test.assert_cp_diff("5a5cea290c048376a9d14e176125b264")


def test_cache():
    """
    Tests the LogBuilder's cache shortcuts
    """
    details = {}
    log = LogBuilder.run(out_details=details)
    builder = details["builder"]
    assert "val" not in builder
    builder["val"] = 123
    assert "val" in builder
    assert builder["val"] == 123
    del builder["val"]
    assert "val" not in builder


def test_run():
    """
    Tests running the log builder directly
    """

    class MyBuilder(LogBuilder):
        @cell
        def hello(self):
            self.text("hello")

    with pytest.raises(ValueError):
        MyBuilder.run(filetype="html", as_service=False, auto_reload=True)

    with pytest.raises(ValueError):
        MyBuilder.run(filetype="html", as_service=True)

    details = {}
    MyBuilder.run(filetype="html", as_service=True, test=True, out_details=details)
    assert details["log"].server is not None


def test_no_module():
    details = {}

    class MyBuilder(LogBuilder):
        @cell
        def hello(self):
            self.text("hello")

    MyBuilder.run(out_details=details)
    builder: LogBuilder = details["builder"]

    """Test if builder also works without known initial module"""
    builder.target_log.initial_module = None
    builder.build()
