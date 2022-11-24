"""
Tests the FileSinkZip archives which allows the easy bundling of data in a zip
archive.
"""
import pytest

from scistag.filestag import FileSink, MemoryZip
from scistag.filestag.sinks.archive_file_sink import ArchiveFileSinkProto


def test_archive():
    """
    Tests archive base methods
    """
    proto = ArchiveFileSinkProto("target")
    with pytest.raises(NotImplementedError):
        proto.store("testfile.bin", b"123")


def test_filesink_zip():
    """
    Tests the basic storage methods
    """
    target = FileSink.with_target("zip://")
    with target:
        target.store("testa.bin", b"123")
        assert not target.store("testa.bin", b"123", overwrite=False)
    reloaded = MemoryZip(target.get_value())
    assert reloaded.read("testa.bin") == b"123"
