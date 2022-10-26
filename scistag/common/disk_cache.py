"""
Implements the class :class:`DiskCache` which allows you to fast and easy
store / dump data such as transformed Pandas dataframes or numpy objects
on disk and to quickly restore them afterwards with a simple version
management.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any

from scistag.common import StagLock
from scistag.filestag import FileStag, Bundle
from scistag.common.cache import Cache

BUNDLE_EXTENSION = ".stbun"
"File extension for a SciStag bundle"


class DiskCache:
    """
    Helper class to persist data such as computation results on disk.

    This class is usually not used directly, see :class:`Cache` which makes
    use of the DiskCache. All elements you store with a beginning "./"
    using the **Cache** class will automatically be stored on disk, all
    entries without in memory.
    """

    def __init__(self,
                 version: int = 1,
                 cache_dir: str | None = None):
        """
        :param version: The cache version. 1 by default.

            When ever you change this version all old cache values will be
            removed and/or ignored from the cache.
        :param cache_dir: The directory in which the data shall be cached
        """
        if cache_dir is None:
            os.path.abspath("./.stscache")
        self.cache_dir = cache_dir
        self._version = version
        """
        The cache version.

        It is stored along all cache values stored on disk and only elements
        sharing the same version will be accepted. 
        """
        self._access_lock = StagLock()
        self.valid = cache_dir is not None
        """
        Defines if the cache is valid
        """
        self.dir_created = False

    @property
    def version(self) -> int:
        """
        Returns the cache version
        """
        return self._version

    @staticmethod
    def encode_name(name):
        """
        Encodes the name of the object to be cached to a unique hash

        :param name: The name of the data
        :return: The encoded name
        """
        encoded_name = hashlib.md5(name.encode("utf-8")).hexdigest()
        return encoded_name

    def get_cache_name(self, name):
        """
        Encodes the name of the object to be cached to a unique hash

        :param name: The name of the data
        :return: The encoded name
        """
        if not self.valid:
            raise AssertionError(
                "Disk cache not configured. Please provide a valid cache_dir.")
        encoded_name = f"{self.cache_dir}/{self.encode_name(name)}"
        return encoded_name

    def _ensure_cache_dir(self):
        """
        Verifies the caching directory is present
        """
        with self._access_lock:
            if not self.dir_created:
                os.makedirs(self.cache_dir, exist_ok=True)

    def set(self, key: str, value: Any, params: dict, version: int = 1):
        """
        Persists a single value in the cache

        :param key: The name of the object to cache or a combination of
            key and version separated by an @ sign, e.g. "database@1"
        :param value: The element's value
        :param version: The cache version for this entry.
        :param params: The creation parameters which were passed into
            the loading function and should match upon a cache fetch try.
        """
        key, eff_version = Cache.get_key_and_version(key,
                                                     self._version,
                                                     version)
        with self._access_lock:
            params = dict(params)
            params["__version"] = eff_version
            with self._access_lock:
                self._ensure_cache_dir()
                cache_name = self.get_cache_name(key)
                bundle_fn = cache_name + BUNDLE_EXTENSION
                FileStag.save(cache_name,
                              Bundle.bundle({"data": value,
                                             "version": 1}))
                FileStag.save(bundle_fn, Bundle.bundle(params))

    def get(self, key, params: dict = None, version: int = 1,
            default=None) -> Any | None:
        """
        Tries to read an element from the disk cache.

        :param key: The name of the object to load from cache or a combination
            of key and version separated by an @ sign, e.g. "database@1"
        :param params: The creation parameters which were passed into
            the loading function and still should match.
        :param version: The assumed version of this element we are searching
            for. If the version does not match the old entry is ignored.
        :param default: The default value to return if no cache entry could
            be found
        :return: Either the cache data or the default value as fallback
        """
        with self._access_lock:
            key, eff_version = Cache.get_key_and_version(key,
                                                         self._version,
                                                         version)
            cache_name = self.get_cache_name(key)
            if params is None:
                params = {}
            params = dict(params)
            with self._access_lock:
                params["__version"] = eff_version
                stored_params = {}
                bundle_fn = cache_name + BUNDLE_EXTENSION
                bundle_data = Bundle.unpack(FileStag.load(cache_name))
                assert bundle_data.get("version", 0) == 1
                data = bundle_data["data"]
                if data is None:
                    return default
                if FileStag.exists(bundle_fn):
                    stored_params = Bundle.unpack(FileStag.load(bundle_fn))
                if stored_params != params:
                    return default
                return data

    def delete(self, key) -> bool:
        """
        Deletes a single cache entry

        :param key: The cache's key
        :return: True if the element was found and deleted
        """
        with self._access_lock:
            cache_name = self.get_cache_name(key)
            bundle_fn = cache_name + BUNDLE_EXTENSION
            FileStag.delete(bundle_fn)
            if FileStag.exists(cache_name):
                return FileStag.delete(cache_name)
            return False

    def __contains__(self, key):
        if not self.valid:
            return False
        with self._access_lock:
            key, eff_version = Cache.get_key_and_version(key, self._version)
            cache_name = self.get_cache_name(key)
            return FileStag.exists(cache_name)
