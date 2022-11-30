"""
Tests the FileObserver class
"""
import shutil
import time

from scistag.filestag import FileStag, FilePath, FileSource, FileObserver


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
    fs_obs = FileObserver(source, max_content_size=8,
                          refresh_time_s=0.04)
    hash_val = fs_obs.__hash__()
    assert fs_obs.__hash__() == hash_val
    FileStag.save(tar_dir + "/testb.bin", b"789")
    time.sleep(0.05)
    assert hash_val != fs_obs.__hash__()
    hash_val = fs_obs.__hash__()
    time.sleep(0.05)
    FileStag.save(tar_dir + "/testc.bin", b"555")
    assert hash_val != fs_obs.__hash__()
