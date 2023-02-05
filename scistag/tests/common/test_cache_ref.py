"""
Tests the class :class:CacheRef which allows creating a link to a specific cache entry
to modify it remotely.
"""
from scistag.common import Cache, CacheRef


def test_cache_ref():
    """
    Tests the CacheRef base functionality
    """
    cache = Cache()
    ref: CacheRef = cache.create_ref("value")
    assert "value" not in cache
    ref.set(456)
    assert cache["value"] == 456
    ref = cache.create_ref("list")
    ref.push(456)
    assert ref.pop("list") == 456
    ref: CacheRef = cache.create_ref("alist", update_async=True)
    ref.push(456)
    assert "alist" not in cache
    vref: CacheRef = cache.create_ref("avalue", update_async=True)
    vref.set(222)
    assert "avalue" not in cache
    cache.async_fetch()
    assert cache["avalue"] == 222
    assert cache.pop("alist") == 456
