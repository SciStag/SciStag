"""
Implements the class CLRef which binds a virtual attribute of a LogBuilder to
a variable in the :class:`Cache` class.
"""

from __future__ import annotations
from typing import Any


class CLRef:
    """
    Binds a LogBuilder attribute to a cache entry
    """

    def __init__(
        self,
        default_value: Any = None,
        key_name: str | None = None,
        create: bool = True,
    ):
        """
        :param key_name: The name of the key to overwrite. If None is defined the
            key name of the attribute will be used.
        :param default_value: The default value. Will overwrite the cache entry if it
            does not exist yet.
        :param create: Defines if the cache value shall be written if it does not exist
            yet.
        """
        self._default_value = default_value
        """The initial value to write into the cache. Will be cleared (inside this
        object) as soon as the reference is initialized."""
        self._key_name = key_name
        """The name in the cache to write to"""
        self._init = create
        """Defines if the value shall be written into the cache if it does not exist
        yet"""
