"""
Tests the DiskCache class
"""
import shutil

from scistag.common.disk_cache import DiskCache


def test_disk_cache_basics(tmp_path):
    """
    Tests the base functionality
    """
    dc_tmp = str(tmp_path) + "/disk_cache"
    try:
        shutil.rmtree(dc_tmp)
    except FileNotFoundError:
        pass
    disk_cache = DiskCache(cache_dir=dc_tmp)
    disk_cache.set("testValue", "123")
    assert disk_cache.get("testValue", default="456") == "123"
    assert "testValue" in disk_cache
    assert "testValueX" not in disk_cache
    assert disk_cache.get("testValueNotExisting", default="456") == "456"
    assert disk_cache.delete("testValue")
    assert disk_cache.get("testValue", default="456") == "456"
    assert not disk_cache.delete("testValue")
