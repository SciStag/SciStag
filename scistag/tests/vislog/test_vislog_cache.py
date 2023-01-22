"""
Tests the VisualLog's test functionality
"""
from scistag.vislog import VisualLog


def test_log_cache():
    """
    Tests the basic cache functions
    """
    options = VisualLog.setup_options()
    options.cache.dir = "./temp/testlogcache"
    log = VisualLog(options=options)
    log.cache.clear()
    log.cache.set("$diskValue", 123)
    assert log.cache.get("$diskValue") == 123
    log.cache.clear()
    assert log.cache.get("$diskValue") is None
    log.cache.set("$diskValue", 123)
    options = VisualLog.setup_options()
    options.cache.dir = "./temp/testlogcache"
    other_log = VisualLog(options=options)
    assert other_log.cache.get("$diskValue") == 123
    options.cache.dir = "./temp/testlogcache"
    options.cache.name = "subCache"
    third_log = VisualLog(options=options)
    assert third_log.cache.get("$diskValue") is None
