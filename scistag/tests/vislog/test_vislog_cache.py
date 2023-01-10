"""
Tests the VisualLog's test functionality
"""
from scistag.vislog import VisualLog


def test_log_cache():
    log = VisualLog(cache_dir="./temp/testlogcache")
    log.cache.clear()
    log.cache.set("$diskValue", 123)
    assert log.cache.get("$diskValue") == 123
    log.cache.clear()
    assert log.cache.get("$diskValue") is None
    log.cache.set("$diskValue", 123)
    other_log = VisualLog(cache_dir="./temp/testlogcache")
    assert other_log.cache.get("$diskValue") == 123
    third_log = VisualLog(cache_dir="./temp/testlogcache", cache_name="subCache")
    assert third_log.cache.get("$diskValue") is None
