"""
Tests the Cache class
"""
import numpy as np
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
    cache.set("$diskKey", 124)
    assert cache.get("$diskKey") == 124
    del cache["$diskKey"]
    assert cache.get("$diskKey") is None
    cache.set("$diskKey@2", 124)
    assert "$diskKey" in cache
    assert cache.get("$diskKey@2") == 124
    assert cache.get("$diskKey@3") is None


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
    cache.set("$diskValue", 123)
    assert cache["$diskValue"] == 123
    assert "$diskValue" in cache
    cache.clear()
    assert "value" not in cache
    assert "$diskValue" not in cache


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


def test_revision():
    """
    Tests the Cache's revision system
    """
    cache = Cache()
    assert cache.get_revision("key") == 0
    cache["key"] = 0
    assert not cache.non_zero("key")
    assert cache.get_revision("key") == 1
    cache["key"] = 1
    assert cache.non_zero("key")
    assert cache.get_revision("key") == 2
    del cache["key"]
    assert cache.get_revision("key") == 3
    cache.increase_revision("key", _already_locked=True)
    assert cache.get_revision("key") == 4
    cache.increase_revision("key", _already_locked=False)
    assert cache.get_revision("key") == 5


def test_list():
    """
    Test list features
    """
    cache = Cache()
    assert cache.lpop("list") == []
    cache.lpush("list", "firstValue")
    assert cache.get_revision("list") == 1
    assert cache.non_zero("list")
    cache.lpush("list", "value")
    assert cache.get_revision("list") == 2
    cache.lpush("list", "lastValue")
    assert cache.llen("list_not_existing") == 0
    assert cache.llen("list") == 3
    assert cache.lpop("list") == ["firstValue"]
    assert cache.get_revision("list") == 4
    with pytest.raises(ValueError):
        assert cache.lpop("list", count=-2) == ["value", "lastValue"]
    with pytest.raises(ValueError):
        assert cache.lpop("list", -2) == ["value", "lastValue"]
    with pytest.raises(ValueError):
        cache.lpop("list", -3)
    assert cache.lpop("list", -2, 2) == ["value", "lastValue"]
    cache.lpush("list", "someValue", "value", "anotherLastValue")
    assert cache.lpop("list", -2, 2) == ["value", "anotherLastValue"]
    assert cache.lpop("list", count=0) == []
    assert cache.lpop("list", 0) == ["someValue"]
    with pytest.raises(ValueError):
        cache.lpop("list", count=-3)
    cache.lpush("list", [123, 456], unpack=True)
    assert cache.lpop("list", count=2) == [123, 456]
    cache.lpush("list", 456, 789)
    assert cache.lpop("list", count=2) == [456, 789]
    cache["text"] = "123"
    with pytest.raises(ValueError):
        assert cache.llen("text")
    with pytest.raises(ValueError):
        assert cache.lpop("text")
    with pytest.raises(ValueError):
        assert cache.lpush("text", 123)
    with pytest.raises(ValueError):
        assert cache.lpush("list", "123", unpack=True)


def test_inc_dec():
    """
    Test increase and decrease
    """
    cache = Cache()
    assert cache.get("value", 0) == 0
    cache.inc("value", 1.0)
    assert cache.get("value", 0) == 1.0
    assert isinstance(cache.get("value"), float) and not isinstance(
        cache.get("value"), int
    )
    cache.inc("value", 1.0)
    assert isinstance(cache.get("value"), float) and not isinstance(
        cache.get("value"), int
    )
    cache.inc("intValue", 3)
    assert cache.get("intValue", 0) == 3
    assert isinstance(cache.get("intValue"), int) and not isinstance(
        cache.get("intValue"), float
    )
    cache.dec("intValue", 2)
    assert cache.get("intValue", 0) == 1
    assert cache.dec("unknownValue", 2) == -2


def test_non_zero():
    """
    Tests the non-zero feature
    """
    cache = Cache()
    assert not cache.non_zero("value")
    cache["value"] = 1
    assert cache.non_zero("value")
    cache["value"] = []
    assert not cache.non_zero("value")
    cache["value"] = [1]
    assert cache.non_zero("value")
    cache["value"] = {}
    assert not cache.non_zero("value")
    cache["value"] = {"value": 123}
    assert cache.non_zero("value")
    cache["value"] = np.array([])
    assert not cache.non_zero("value")
    cache["value"] = np.array([123, 456])
    assert cache.non_zero("value")

    class MyIncompatibleClass:
        """For testing"""

    cache["value"] = MyIncompatibleClass()
    assert not cache.non_zero("value")


def test_remove():
    """
    Tests the remove functionality
    :return:
    """
    cache = Cache()
    cache["myValue"] = 123
    cache["myGroup.valueA"] = 123
    cache["myGroup.valueB"] = 123
    assert "myValue" in cache
    assert "myGroup.valueA" in cache
    cache.remove("myGroup.*")
    assert "myValue" in cache
    assert "myGroup.valueA" not in cache
    cache["myGroup.valueA"] = 123
    cache["myGroup.valueB"] = 123
    cache["myGroup.valueC"] = 123
    del cache["myGroup.valueC"]
    cache.remove(["myGroup.*"])
    assert "myValue" in cache
    cache.remove("myValue")
    assert "myValue" not in cache
    cache.remove("doesntExist")
