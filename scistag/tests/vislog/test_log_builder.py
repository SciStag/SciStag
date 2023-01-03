"""
Advance LogBuilder tests
"""
import pytest

from scistag.vislog import VisualLog, LogBuilder


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
    assert b"Test" in log_b.default_builder.create_backup().data
    log_c = VisualLog(formats_out={"txt"})
    with pytest.raises(ValueError):
        log_c.default_builder.create_backup()


def test_static_file():
    log_a = VisualLog()
    builder = log_a.default_builder
    builder.service.publish("testFile.bin", b"Hello world")
    assert builder.service.get_file("testFile.bin").body == b"Hello world"
