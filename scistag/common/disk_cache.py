from __future__ import annotations

import hashlib
import os
from typing import Any

from scistag.common import StagLock
from scistag.filestag import FileStag, Bundle

BUNDLE_EXTENSION = ".bundle"


class DiskCache:
    # TODO Work in progress

    def __init__(self, cache_dir: str | None = "./.cache"):
        """
        :param cache_dir: The directory in which the data shall be cached
        """
        self.cache_dir = cache_dir
        self._access_lock = StagLock()
        self.valid = cache_dir is not None
        """
        Defines if the cache is valid
        """
        self.dir_created = False

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
        with self._access_lock:
            if not self.dir_created:
                os.makedirs(self.cache_dir, exist_ok=True)

    def set(self, key: str, value: Any, parameters: dict):
        """
        Persists a single value in the cache

        :param key: The name of the object to cache
        :param value: The element's value
        :param parameters: The creation parameters, including the version
            number.
        """
        with self._access_lock:
            self._ensure_cache_dir()
            cache_name = self.get_cache_name(key)
            bundle_fn = cache_name + BUNDLE_EXTENSION
            FileStag.save(cache_name, Bundle.bundle({"data": value,
                                                     "version": 1}))
            FileStag.save(bundle_fn, Bundle.bundle(parameters))

    def get(self, key, params: dict = None) -> Any | None:
        cache_name = self.get_cache_name(key)
        with self._access_lock:
            if params is None:
                params = {}
            cur_params = {}
            bundle_fn = cache_name + BUNDLE_EXTENSION
            bundle_data = Bundle.unpack(FileStag.load(cache_name))
            assert bundle_data.get("version", 0) == 1
            data = bundle_data["data"]
            if data is None:
                return None
            if FileStag.exists(bundle_fn):
                cur_params = Bundle.unpack(FileStag.load(bundle_fn))
            if cur_params != params:
                return None
            return data

    def delete(self, key) -> bool:
        with self._access_lock:
            cache_name = self.get_cache_name(key)
            bundle_fn = cache_name + BUNDLE_EXTENSION
            FileStag.delete(bundle_fn)
            if FileStag.exists(cache_name):
                return FileStag.delete(cache_name)
            return False

    def __contains__(self, key):
        cache_name = self.get_cache_name(key)
        return FileStag.exists(cache_name)
