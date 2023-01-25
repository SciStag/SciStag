"""
Defines the class :class:`CacheRef` which defines the reference to a specific target
key in a cache.

Such a reference may be provided to helper threads to deliver results or receive tasks
asynchronously from the main or another thread.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.common.cache import Cache


class CacheRef:
    """
    Defines a reference to a single cache value.

    This reference can for example be used to share it with a worker thread.
    """

    def __init__(self, cache: "Cache", name: str, update_async: bool = False):
        """
        :param cache: The target cache
        :param name: The entry key
        :param update_async: Defines if the element is accessed asynchronous. If so the
            value will be updated once the owning thread regains control.
        """
        self.cache: Cache = cache
        self.name = name
        self.is_async = update_async

    def set(self, value):
        """
        Sets the cache value

        :param value: The new value
        """
        if self.is_async:
            self.cache.set_async(self.name, value)
        else:
            self.cache.set(self.name, value)

    def pop(self, default=None, index: int = 0) -> Any | None:
        """
        Tries to receive a single value from the cache.

        The source can either be a single value or a list. If it's a list the value
        is removed from the list. If it's a single value the whole value will be
        removed.

        :param default: The default value to return if the list is empty or the key
            does not exist
        :param index: The index from which the data shall be fetched. 0 = start of the
            list, -1 = end of the list.
        :return: The value if it could be received
        """
        return self.cache.pop(self.name, default=default, index=index)

    def push(self, value):
        """
        Pushes a value to the target, e.g. a result list

        :param value: The value to push to the list
        """
        if self.is_async:
            self.cache.lpush_async(self.name, value)
        else:
            self.cache.lpush(self.name, value)
