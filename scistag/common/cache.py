"""
Implements the :class:`Cache` class which allows easy caching data on disk
and in memory to minimize repetitive downloads and re-computations.
"""
from __future__ import annotations

import hashlib
import time
from fnmatch import fnmatch

from typing import Any, Callable

from scistag.common.mt.stag_lock import StagLock


class Cache:
    """
    The Cache class shall help caching computation results, downloaded data
    but also objects with large wind-up time (such as neural networks) between
    execution sessions.

    ..  code-block: python

        # caching in memory without version
        my_cache = Cache()
        def complex_computation():
            time.sleep(5.0) # just as dummy
            return np.ones((8,8), dtype=float)
        def rendering_function()
            global my_cache
            my_data = my_cache.cache("data", complex_computation)
            display(my_data)

        rendering_function()  # will take 5.0 seconds on the first run
        rendering_function()  # 0 seconds as "data" will be found in the cache

        # with version - all cache entries !=5 will be ignored
        my_cache = Cache(version=5)  # only cache entries with 5 will be valid
        ...

        # with per-element or "sub"-version.
        # the cache will always combine the cache object's version and the
        # version of the element. So in this case to "5.4"
        def rendering_function()
            global my_cache
            my_data = my_cache.cache("data@4", complex_computation)
            # or
            # my_data = my_cache.cache("data", complex_computation, version=4)
            display(my_data)

        # caching on disk between execution runs
        # if you run the cache "manually" you have to set a version number to
        # cache data between multiple execution sessions on disk.
        my_data = my_cache.cache("./data@5", complex_computation)

    If you pass a version of 0 the :meth:`get_app_session_id` will
    be used instead which will usually change on every restart except
    you set it yourself via set_app_session_id or are using a smart
    autoreloader such as VisualLog's auto-reload capabilities which
    ensure this for you.
    """

    _app_session_id: int = int(time.time() * 1000)
    """
    The current run's session ID. is updated every re-start usually, may
    be stored and restored by helper classes such as the VisualLogAutoReloader
    between application restarts.
    """

    def __init__(self, version: str | int = 1, cache_dir: str = None):
        """
        :param version: The cache version. 1 by default.

            When ever you change this version all old cache values will be
            removed and/or ignored from the cache.
        :param cache_dir: The directory in which the cache data shall be stored
        """
        self._access_lock = StagLock()
        "Multithreading access lock"
        self._mem_cache = {}
        """
        A cache for temporary data storage and objects with a life time bound to
        this component's usage state.

        A cache which whose content shall only live between a handle_load() and
        handle_unload(). This can be used to store data only while a component 
        is being used, a Widget is visible etc. See :meth:`handle_load`.
        """
        self._mem_cache_versions = {}
        "Version numbers for the elements stored in the memory cache"
        from scistag.common.disk_cache import DiskCache

        self._disk_cache = DiskCache(version=version, cache_dir=cache_dir)
        "Cache for persisting data between execution sessions"
        self._version = version
        """
        The cache version.
        
        It is stored along all cache values stored on disk and only elements
        sharing the same version will be accepted. 
        """
        self.loaded = False
        "Defines if the component was correctly loaded"
        self._is_loading = False
        """
        Flag which tells if the component is currently being loaded and if new 
        values added to the cache via ``self["objectName"]`` shall be flagged as 
        volatile.

        During the execution of the :meth:`load` function and their event 
        handlers such as :meth:`Widget.handle_load()` this value is set to true. 
        When new Widgets are added during this time or new values are added to 
        the cache, e.g. via  my_component["data"] = load_data() they are flagged 
        as volatile.

        After the execution of unload() all volatile entries will be deleted 
        from the cache and all widgets added as child will be automatically 
        removed again. 
        """
        self._volatile_cache_entries = set()
        """
        Stores which cache entries shall be deleted upon the execution of 
        :meth:`unload`.

        If a cache entry is added while ``_is_loading`` is set to True it will 
        be added to this set. Upon the execution of ``unload()`` all elements 
        named in this list will be removed from the :attr:`_cache`.

        In addition you may add object member variables via 
        :meth:`add_volatile_member` which do not get removed but automatically 
        cleared upon execution of unload. 
        """
        self._key_revisions = {}
        """
        Version counter for each key
        """

    @property
    def version(self) -> str:
        """
        Returns the cache version
        """
        return str(self._version)

    @classmethod
    def get_app_session_id(cls) -> int:
        """
        Returns the app session id which is generated upon each application
        restart.
        """
        return cls._app_session_id

    @classmethod
    def override_app_session_id(cls, session_id: int):
        """
        Manually overrides the application's session ID.

        Should only be used by application session managers.

        :param session_id: The new session id
        """
        cls._app_session_id = session_id

    @classmethod
    def get_key_and_version(cls, key, major, minor=None) -> tuple[str, str]:
        """
        Returns the effective key, version combination to search for a key in
        combination with the cache's and the element's version.

        :param key: The key (potentially still containing @version at it's end),
            either "key" or "key@version", e.g. "myDb@2".
        :param major: The major version (provided by the cache object)
        :param minor: The minor version, per element.

            Default 0 for memory cache elements and 1 for disk cache entries.
        :return: The effective key and version with which the element shall be
            persisted and which we assume upon restore.

            Following rules apply:
            - minor >= 1: The cache's version and the minor version are
                combined. So if you change either the cache's or the element
                version the element gets invalidated.
            - minor <= -1: The data should be handled as "constant" which
                basically never changes. Changing the cache's version has thus
                no effect, only if you directly change the element's version.
            - minor equals 0: The session's ID will be used as minor version.

                This invalidates all cache entries when you completely close
                the app or service (including auto-restart mechanisms, e.g.
                for live-editing).
        """
        if minor is None:
            minor = 1 if "/" in key else 0
        if "@" in key:
            split_val = key.split("@")
            assert len(split_val) == 2
            key: str = split_val[0]
            minor = split_val[1]
        minor = str(minor)
        if minor == "0":  # session id only as cache version
            return key, f"{major}.{cls._app_session_id}"
        if minor.startswith("-"):  # minor only
            return key, f"{minor}"
        return key, f"{major}.{minor}"

    def cache(self, key: str, generator: Callable, *args, **kwargs):
        """
        Tries to find the element **key** in the cache and return's it's
        content. If no element with such a name and/or version number can be
        found **generator** be called to generate the data, store it in the
        cache for the next execution.

        :param key: The key of the cache element
        :param generator: The function to call if the element is not stored
            in the cache yet.
        :keyword version: The version to assign to the cache entry. If either
            this or the cache's main version get modified all prior cache
            entries will be ignored until they were update to this new version.

            Default version for memory cache entries is 0, for disk cache
            entries 1.
        :keyword hash_val: A single value, a list of values or a dict of values
            of which a hash value is computed and added to the version
            number to automatically invalidate it if any of the values
            changed.
        :param args: Argument parameters to be passed into the generator
        :param kwargs: Keyword parameter to be passed into the generator
        :return: The cached or newly created content
        """
        hash_val = kwargs.pop("hash_val", None)
        version = kwargs.pop("version", None)
        if hash_val is not None:
            version = str(version) if version else "0"
            version += "#" + hash_val
        arg_list = list(args)
        # try to fetch from cache
        with self._access_lock:
            old_value = self.get(key, version=version)
            if old_value is not None:  # cached? fine
                return old_value
        new_data = generator(*arg_list, **kwargs)
        # update cache otherwise
        with self._access_lock:
            self.set(key, new_data, version=version)
            return new_data

    def set(self, key: str, value, version=None) -> Any:
        """
        Adds an item to the cache or updates it.

        If a value is added (for the first time) during the execution of the
        component's ``load()`` or ``handle_load`` method it is flagged as
        volatile and will be automatically removed again upon the
        execution of ``unload()`` / ``handle_unload()``.

        :param key: The item's name
        :param value: The value to assign
        :param version: The version of the cache element. By default 0 for
            memory cache elements and 1 for disk cache elements.
        :return: The assigned value

        """
        with self._access_lock:
            org_key = key
            key, eff_version = self.get_key_and_version(
                key, self._version, minor=version
            )
            assert len(key) > 0
            if (
                not key[0].isalpha()
                and not key.startswith("./")
                and not key.startswith("_")
            ):
                raise ValueError("Keys has to start with a character")
            if key in self._key_revisions:
                self._key_revisions[key] += 1
            else:
                self._key_revisions[key] = 1
            if "/" in key:
                self._disk_cache.set(org_key, value, version=version)
                return value
            # flag of volatile if added during loading process
            if key not in self._mem_cache and self._is_loading:
                self._volatile_cache_entries.add(key)
            self._mem_cache[key] = value
            self._mem_cache_versions[key] = eff_version
            return value

    def get(self, key: str, default=None, version=None):
        """
        Returns a value from the cache.

        If the element does not exist a ValueError exception will be raised.

        :param key: The item's name.
        :param version: The cache element's version.

            By default 0 for memory cache elements and 1 for disk cache
            elements.
        :param default: The value to return by default if no cache element
            could be found.
        :return: The item's value.

        Returns default if no value can be found.
        """
        with self._access_lock:
            org_key = key
            key, eff_version = self.get_key_and_version(
                key, self._version, minor=version
            )
            if "/" in key:
                data = self._disk_cache.get(org_key, version=version)
                if data is None:
                    return default
                return data
            if key in self._mem_cache and self._mem_cache_versions[key] == eff_version:
                return self._mem_cache[key]
            else:
                return default

    def get_revision(self, key) -> int:
        """
        Returns the revision of given cache entry.

        If the value does not exist yet it has a revision of 0 by default.

        :param key: The key of the version to return
        :return: The revision. 0 if the key does not exist.
        """
        with self._access_lock:
            return self._key_revisions.get(key, 0)

    def clear(self):
        """
        Clears the disk cache completely

        """
        with self._access_lock:
            self._mem_cache = {}
            self._mem_cache_versions = {}
        if self._disk_cache is not None:
            self._disk_cache.clear()

    def load(self):
        """
        Call this before you start using a component for the first time. The
        ``scistag.slidestag.widget.Widget`` class does this automatically
        for all of its children when a Widget becomes visible.
        """
        with self._access_lock:
            if self.loaded:
                raise RuntimeError("Tried to load component twice")
            self._is_loading = True
            self.handle_load()
            if not self.loaded:
                raise RuntimeError(
                    "loaded flag of component not correctly set to True. "
                    "Did you forget to call super().handle_load()?"
                )

    def unload(self):
        """
        Call this to unload all data from your component which was created
        during the handle_load execution and not flagged via a slash ("/")
        in its name as element to cache on disk.
        """
        with self._access_lock:
            if not self.loaded:
                raise RuntimeError(
                    "Tried to unload component which was not loaded before"
                )
            self.handle_unload()
            if self.loaded:
                raise RuntimeError(
                    "loaded flag of component not correctly set to False. "
                    "Did you forget to call super().handle_unload()?"
                )
            for element in self._volatile_cache_entries:
                if element.startswith("."):  # clear volatile members
                    member_name = element[1:]
                    if member_name in self.__dict__:
                        self.__dict__[member_name] = None
                # delete volatile cache entries
                elif element in self._mem_cache:
                    del self._mem_cache[element]
                    del self._mem_cache_versions[element]
                    self._key_revisions[element] += 1

    def get_is_loading(self) -> bool:
        """
        Returns if the component is currently being loaded
        :return: True if ``load`` is currently being executed for this
        component.
        """
        with self._access_lock:
            return self._is_loading

    def handle_load(self):
        """
        Event handling function for dynamically loading data on demand.

        SciStag's ``load`` and ``unload`` mechanism shall help minimizing the
        memory footprint of the application using it. If you have temporary
        data, for example a database which is just used while a component is
        used, a Slide or an ImageView while they are visible please overwrite
        this function, call it's ancestor and then store your data in the
        "cache".

        You can do so by using the bracket operator like ``self['db'] =
        pd.read_csv(...)``, check if data is
        available via ``if 'db' in self: ...`` and access it via ``my_db =
        self['db']`` accordingly.

        All data stored this way will automatically get cleared and removed from
        the cache when the `unload` function
        is called, e.g. when the Slide or Widget disappears or when you call it
        for your custom component.

        If you want to use member variables for storing your temporary data you
        can do so by calling
        :meth:`add_volatile_member` and passing their name. Upon unloading
        ``None`` will be assigned to all
        registered variables.

        **Note**: When overwriting this method call ``super().handle_load()``
        at the beginning of yours.
        """
        with self._access_lock:
            self.loaded = True

    def handle_unload(self):
        """
        Event handler for unloading elements previously loaded in your
        handle_load function.

        **Note**: When overwriting this method call ``super().handle_unload()``
        at **end** beginning of yours.
        """
        with self._access_lock:
            self.loaded = False

    def add_volatile_member(self, name: str) -> None:
        """
        Adds a member to the volatile cache entry variable list so it can
        automatically be cleared upon unloading of this component.

        When the component is unloaded (e.g. because a Widget or a Slide
        disappears) all members are automatically set to None to prevent that
        these objects are kept alive.

        :param name: The name of the member variable to be added to the volatile
        list.
        """
        with self._access_lock:
            self._volatile_cache_entries.add("." + name)

    def __setitem__(self, key: str, value):
        self.set(key, value)
        return value

    def __getitem__(self, key) -> Any:
        with self._access_lock:
            result = self.get(key)
            if (
                result is None
                and key not in self._mem_cache
                and key not in self._disk_cache
            ):
                raise KeyError(f"Key {key} not found")
            return result

    def inc(self, key, value: float | int = 1):
        """
        Increases given cache value.

        If the value does not exist yet, it will be created

        :param key: The key to increase
        :param value: The value by which the value shall be increased
        :return: The new value
        """
        with self._access_lock:
            if key in self:
                new_value = self[key] + value
                self[key] = new_value
                return new_value
            else:
                self[key] = value
                return value

    def dec(self, key, value: float | int):
        """
        Decreases given cache value.

        If the value does not exist yet, it will be created

        :param key: The key to increase
        :param value: The value by which the value shall be decreased
        :return: The new value
        """
        with self._access_lock:
            if key in self:
                new_value = self[key] - value
                self[key] = new_value
                return new_value
            else:
                self[key] = -value
                return value

    def lappend(self, key: str, value: Any, unpack: bool = False):
        """
        Appends the value provided to the list named key.

        If the list does not exist yet it will be created

        :param key: The key of the list
        :param value: The value to be added
        :param unpack: Defines if value is a list and all of its elements shall be
            added to the target list
        """
        with self._access_lock:
            if key not in self:
                tar_list = self[key]
                self.increase_revision(key, True)
            else:
                tar_list = []
                self[key] = tar_list
            if not isinstance(tar_list, list):
                raise ValueError(
                    f"Tried to append new values to non-list " f"element {key}"
                )
            if unpack:
                if not isinstance(value, list):
                    raise ValueError("Can only unpack lists")
                tar_list.extend(value)
            else:
                tar_list.append(value)

    def lpop(self, key: str, count: int = 1, index: int = -1):
        """
        Pops one or multiple values from the list

        :param key: The key of the list
        :param count: The count of values to pop.

            If a count of -1 is passed all values will be received.
        :param index: The index from which the value shall be received.

            At the moment only 0 (from list front) and -1 (from end) are supported.
        :return: A list of all values received.

            An empty list if the list does not exist
        """
        with self._access_lock:
            if key not in self:
                return []
            src_list = self[key]
            if not isinstance(src_list, list):
                raise ValueError(f"Tried to pop values from non-list element {key}")
            if count >= len(src_list) or count == -1:
                results = src_list
                self.increase_revision(key)
            else:
                if index != 0 and index != -1:
                    raise ValueError(
                        "At the moment only values of 0 and -1 are"
                        "supported as source index"
                    )
                if index == -1:
                    results = src_list[-count:]
                    end = len(src_list) - count
                    self[key] = src_list[0:end]
                else:
                    results = src_list[0:count]
                    self[key] = src_list[count:]
            return results

    def llen(self, key: str) -> int:
        """
        Receives the length of the list with given name

        :param key: The list's name in the cache
        :return: The list's length if the list is known, 0 otherwise.
        """
        with self._access_lock:
            if key not in self:
                return 0
            src_list = self[key]
            if not isinstance(src_list, list):
                raise ValueError(f"Tried to receive length of non-list element {key}")
            return len(src_list)

    def increase_revision(self, key, locked=False):
        """
        Increases the version of given key

        :param key: The key to modify
        :param locked: Defines if we are already locked
        :return: The new version
        """
        if locked:
            self._mem_cache_versions[key] += 1
            return self._mem_cache_versions[key]
        else:
            with self._access_lock:
                self._mem_cache_versions[key] += 1
                return self._mem_cache_versions[key]

    def remove(self, keys: str | list[str]) -> int:
        """
        Removes the key or keys matching the name or the name mask provided.

        You can use * and ? to remove a set of cache entries in one go.

        In difference to a del cache["keyName"] the remove method fails silently
        and though can be used pretty well to do a "cleanup" w/o additional check
        for existence.

        :param keys: A single name or a list of names of keys to remove.

            Can contain placeholders such as * and ?
        :return: The number of elements deleted
        """
        with self._access_lock:
            if isinstance(keys, str):
                keys = [keys]
            remove_set = set()
            for element in keys:
                if "?" in element or "*" in element:
                    for cur_key in self._key_revisions.keys():
                        if fnmatch(cur_key, element):
                            remove_set.add(element)
                else:
                    if element in self._key_revisions:
                        remove_set.add(element)
            for element in remove_set:
                del self[element]

            return len(remove_set)

    def non_zero(self, key: str) -> bool:
        """
        Returns if the element has a non-zero size

        :param key: The key of the element to check
        :return True: If the element does exist and has a size or length > 0
        """
        with self._access_lock:
            if key not in self:
                return False
            element = self[key]
            if isinstance(element, (float, bool, int)):
                return element != 0
            if isinstance(element, (str, dict, list, bytes)):
                return len(element) > 0
            if hasattr(element, "shape"):  # np.ndarray and DataFrame
                return element.shape[0] > 0
            return False

    def __delitem__(self, key):
        """
        Deletes an element from the cache.

        Does raise a value error if the key does not exist yet.

        :param key: The element's name
        """
        with self._access_lock:
            key, eff_version = self.get_key_and_version(key, self._version)
            if "/" in key:
                self._disk_cache.delete(key)
                return
            if key not in self._mem_cache:
                return
            del self._mem_cache[key]
            self._key_revisions[key] += 1

    def __contains__(self, key) -> bool:
        """
        Returns if an element exists in the cache.

        :param key: The item's name
        :return: True if the item exists.
        """
        with self._access_lock:
            key, eff_version = self.get_key_and_version(key, self._version)
            if "/" in key:
                return key in self._disk_cache
            return (
                key in self._mem_cache and self._mem_cache_versions[key] == eff_version
            )


_cache_access_lock = StagLock()
"Cache creation lock"
_global_cache: Cache | None = None
"Shared, singleton global cache"


def get_global_cache() -> Cache:
    """
    Returns the shared global cache class. When storing data categorize it
    w/ a main module and sub module to track memory usage of the shared cache.

    :return: The global cache
    """
    global _global_cache
    with _cache_access_lock:
        if _global_cache is None:
            _global_cache = Cache()
        return _global_cache
