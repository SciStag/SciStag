"""
Implements the :class:`DataCache` for intelligent data and computation
caching.
"""

from __future__ import annotations
from typing import Callable, Any

from scistag.common.mt.stag_lock import StagLock


class DataCache:
    """
    A class which temporarily caches values, e.g. a loaded DataFrame or a
    rendered text using a simple "execute function if the value does not
    exist yet" to easily process data on demand only.
    """

    global_cache: DataCache | None = None
    """
    The global cache dictionary to temporary store computations.
    
    Use with care and always prefer session or slide specific caches for
    automatic unloading cached data when it's not needed anymore.
    """

    def __init__(self, thread_safe: bool = False):
        """
        Initializer

        :param thread_safe: Defines if the cache has to be thread safe.
            False by default for UI / linear execution caches such as in
            SlideStag.
        """
        self.dict_cache = {}
        self.access_lock = StagLock(thread_lock=thread_safe)

    def __contains__(self, item):
        """
        Returns if a specific item exists

        :param item: The item's name
        :return: True if it does
        """
        with self.access_lock:
            return item in self.dict_cache

    def __getitem__(self, item) -> Any | None:
        """
        Returns an item if it exists

        :param item: The item's name
        :return: The item's data
        """
        with self.access_lock:
            if item in self.dict_cache:
                return self.dict_cache[item]['data']
            return None

    def get(self, item: str, default: Any = None) -> Any | None:
        """
        Returns an item if it exists

        :param item: The item's name
        :param default; The default value
        :return: The item's data if it exists, returns default otherwise
        """
        with self.access_lock:
            if item in self.dict_cache:
                return self.dict_cache[item]['data']
            return default

    def __setitem__(self, key, value):
        with self.access_lock:
            self.dict_cache[key] = {"data": value,
                                    "parameters": None}

    def cache(self, identifier: str, builder: Callable[[Any], Any] | None,
              parameters: Any | None = None,
              overwrite: bool = False) -> Any:
        """
        Tries to retrieve given element from cache and generates it's data
        otherwise.

         If the element is not stored
        in the cache it will be created using the builder callback which should
        await a single parameter and return a single value.
        If parameters (optional) is passed it will be verified if the parameters
        were modified.

        :param identifier: The identifier. Either a string or a dictionary
            with a configuration.
        :param builder: The function to call if the value does not exist
        :param parameters: If the data may dynamically change using the same
            identifier, pass it too
        :param overwrite: If set to true the previous value will be replaced
        :return: The data
        """
        if not isinstance(identifier, str):
            raise ValueError("Invalid identifier type")
        with self.access_lock:
            if identifier in self.dict_cache and not overwrite:
                element = self.dict_cache[identifier]
                if element['parameters'] is None:
                    return element['data']
                if element['parameters'] is not None and parameters is not None:
                    if element['parameters'] == parameters:
                        return element['data']
            new_data = builder(
                parameters) if parameters is not None else builder()
            self.dict_cache[identifier] = {'data': new_data,
                                           'parameters': parameters}
            return new_data

    def remove(self, names: str | list[str]) -> None:
        """
        Removes one or multiple elements from the cache
        :param names: The list of names
        """
        with self.access_lock:
            if isinstance(names, str):
                if names in self.dict_cache:
                    del self.dict_cache[names]
            else:
                for cur_name in names:
                    if cur_name in self.dict_cache:
                        del self.dict_cache[cur_name]

    def clear(self):
        """
        Clears the whole cache
        """
        with self.access_lock:
            self.dict_cache = {}


DataCache.global_cache = DataCache(thread_safe=True)
