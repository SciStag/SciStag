"""
Implements the classes :class:`DataObserver` and :class:`DataObserverList` whose
ancestors / implementations allow the observing of databases, data elements
and file sources. See :class:`FileDataObserver` for example.
"""

from __future__ import annotations

import time
from hashlib import md5


class DataObserver:
    """
    The observer class is the base class for observers of file storages and
    databases.

    They are for example used to automatically invalidate :class:"Cache" and
    :class:"DiskCache" objects when any of the files they depend on
    was modified.
    """

    def __init__(self, refresh_time_s: float = 1.0):
        """
        :param refresh_time_s: The minimum time difference between the last
            check before a new complete refresh shall be executed.
        """
        self.refresh_time_s = refresh_time_s
        self.last_update = None
        self._last_hash: int = 0

    def hash_int(self) -> int:
        """
        Returns the hash of the object we are observing as single MD5 string
        """
        raise NotImplementedError("Hash function not implemented")

    def __hash__(self) -> int:
        """
        Returns the observer's hash. When ever a sub element of the observer
        was modified this value will change.

        :return: The hash value
        """
        cur_time = time.time()
        if (
            self.last_update is None
            or cur_time > self.last_update + self.refresh_time_s
        ):
            self._last_hash = self.hash_int()
            self.last_update = cur_time
        return self._last_hash


class DataObserverList(DataObserver):
    """
    Defines a list of observers with multiple data targets.

    The observer's hash will change if any single element changes its
    content and so it's hash value.
    """

    def __init__(
        self, observers: list[DataObserver] | None = None, refresh_time_s: float = 1.0
    ):
        """
        :param observers: The list of observers we shall combine
        :param refresh_time_s: The minimum time gap between a refresh
        """
        super().__init__(refresh_time_s=refresh_time_s)
        self.observers: list[DataObserver] = observers

    def add(self, observer: list[DataObserver] | DataObserver) -> None:
        """
        Adds one or multiple new observers to the list

        :param observer: A single observer or a list of observers
        """
        self.last_update = None  # clear after obvious change
        if isinstance(observer, list):
            self.observers += observer
        else:
            self.observers.append(observer)

    def hash_int(self) -> int:
        hashes = "obsl"
        for element in self.observers:
            hashes += element.__hash__()
        return int(md5(hashes.encode("utf-8")).hexdigest(), 16)
