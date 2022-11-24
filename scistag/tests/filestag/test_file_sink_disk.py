"""
Tests the class FileSinkDisk which can store files to disk
"""
import shutil

from scistag.filestag import FilePath, FileSink


def test_filesink_disk(tmp_path):
    """
    Tests the base methods
    """
    tar_dir = str(tmp_path) + "/fsdisk"
    try:
        shutil.rmtree(tar_dir)
    except FileNotFoundError:
        pass
    FilePath.make_dirs(tar_dir, exist_ok=True)
    disk_sink = FileSink.with_target(tar_dir, create_dirs=False)
    assert not disk_sink.store("subDir/test.bin", b"123")
    disk_sink = FileSink.with_target(tar_dir, create_dirs=True)
    assert disk_sink.store("subDir/test.bin", b"123")
    assert disk_sink.store("subDir/test.bin", b"123")
    assert not disk_sink.store("subDir/test.bin", b"123", overwrite=False)
