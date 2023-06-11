"""
Tests the FileDataObserver class
"""
import shutil
import time

from scistag.common.time import sleep_min
from scistag.filestag import FileStag, FilePath, FileSource, FileDataObserver


def test_file_source_observer(tmp_path):
    """
    Test's the file source's hash functionality
    """
    tar_dir = str(tmp_path) + "/fsobsdir"
    try:
        shutil.rmtree(tar_dir)
    except FileNotFoundError:
        pass
    FilePath.make_dirs(tar_dir, exist_ok=True)
    FileStag.save(tar_dir + "/testa.bin", b"123")
    FileStag.save(tar_dir + "/testb.bin", b"456")
    source = FileSource.from_source(tar_dir, search_mask="*.bin")
    fs_obs = FileDataObserver(source, max_content_size=8, refresh_time_s=0.04)
    hash_val = fs_obs.__hash__()
    assert fs_obs.__hash__() == hash_val
    FileStag.save(tar_dir + "/testb.bin", b"789")
    sleep_min(0.05)
    assert hash_val != fs_obs.__hash__()
    hash_val = fs_obs.__hash__()
    sleep_min(0.05)
    FileStag.save(tar_dir + "/testc.bin", b"555")
    assert hash_val != fs_obs.__hash__()

    source = FileSource.from_source(tar_dir, search_mask="*.bin")
    single_file = str(tmp_path) + "/single_file.bin"
    fs_obs = FileDataObserver(None, max_content_size=8, refresh_time_s=0.04)
    fs_obs.add(source)
    fs_obs.add(single_file)
    FileStag.save(single_file, b"123")
    hash_val = fs_obs.__hash__()
    sleep_min(0.05)
    FileStag.save(single_file, b"456")
    assert hash_val != fs_obs.__hash__()
