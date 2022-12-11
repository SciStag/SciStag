"""
Tests the Cache class
"""
import pytest

from scistag.common import Cache, get_global_cache


def test_basics():
    """
    Tests basic functions
    """
    cache = Cache()
    old_id = Cache.get_app_session_id()
    assert Cache.get_app_session_id() > 0
    cache.set("Value@0", 123)
    assert cache.get("Value@0") == 123
    Cache.override_app_session_id(123)
    assert cache.get("Value@0", default=0) == 0
    assert Cache.get_app_session_id() == 123
    Cache.override_app_session_id(old_id)
    assert Cache.get_app_session_id() == old_id
    assert cache.version == "1"
    cache = Cache(version=3)
    assert cache.version == "3"
    cache = Cache(version="123")
    assert cache.version == "123"
    cache.set("Value@2", 123)
    cache.set("FixValue@-2", 123)
    assert cache.get("Value@2") == 123
    assert cache.get("Value@3", default=5) == 5
    cache._version = 5
    assert cache.get("Value@2", default=0) == 0
    assert cache.get("FixValue@-2", default=0) == 123
    assert isinstance(get_global_cache(), Cache)


def test_set_get():
    """
    Basic set and get caching
    """
    cache = Cache()
    cache.set("key", 124)
    assert cache.get("key") == 124
    assert "key" in cache
    cache.set("./diskKey", 124)
    assert cache.get("./diskKey") == 124
    del cache["./diskKey"]
    assert cache.get("./diskKey") is None
    cache.set("./diskKey@2", 124)
    assert "./diskKey" in cache
    assert cache.get("./diskKey@2") == 124
    assert cache.get("./diskKey@3") is None


def test_cache():
    """
    Tests the usage of cache
    """
    cache = Cache()
    cache.set("key", 124)

    value = 0

    def meth(add_value, second_val):
        nonlocal value
        value += add_value + second_val
        return value

    assert "dynamicValue" not in cache
    val = cache.cache("dynamicValue", meth, 123, second_val=5)
    assert value == 128
    assert val == 128
    assert "dynamicValue" in cache

    val = cache.cache("dynamicValue", meth, 123, 46)
    assert value == 128
    assert val == 128

    val = cache.cache("dynamicValue", meth, 123, 3, hash_val="45")
    assert value == 254
    assert val == 254


def test_clear():
    """
    Tests the clearing functionality of the cache
    """
    cache = Cache()
    cache.set("value", 123)
    assert cache["value"] == 123
    assert "value" in cache
    cache.set("./diskValue", 123)
    assert cache["./diskValue"] == 123
    assert "./diskValue" in cache
    cache.clear()
    assert "value" not in cache
    assert "./diskValue" not in cache


def test_load_unload():
    """
    Tests the load and unload behavior of properties
    """

    class DummyCache(Cache):
        def __init__(self):
            super().__init__()
            self.no_unload = False

        def handle_load(self):
            super().handle_load()
            self["tempValue"] = 123
            self["tempValue2"] = 123

        def handle_unload(self):
            if not self.no_unload:
                super().handle_unload()

    cache = DummyCache()
    cache.load()
    assert cache["tempValue"] == 123
    del cache["tempValue2"]
    cache.unload()
    assert "tempValue" not in cache

    cache = DummyCache()
    cache.no_unload = True
    cache.load()
    with pytest.raises(RuntimeError):
        cache.unload()
