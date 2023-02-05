"""
Implements :class:`LogBuilderBase` - the foundation of the log builder class
"""

from __future__ import annotations

from typing import Any

from .cache_log_ref import CLRef
from ...common import Cache


class LogBuilderBase:
    """
    Defines the foundation of the log builder classes and implements some basic
    data structures and methods.
    """

    def __init__(self):
        super().__init__()
        """Initializer"""
        self.cache = Cache()
        """The local data cache"""
        self._bindings = {}
        """Defines the cache bindings which are used to connect LogBuilder attribute
        names to values in the cache"""

    @classmethod
    def clref(
        cls, default=None, key_name: str | None = None, create: bool = True
    ) -> Any:
        """
        Creates a binding to a cache value and (if it does not exist yet) initializes
        it with the default value provided.

        This binding only works in conjunction with assigning it to a LogBuilder
        attribute.

        ..  code-block:python:

            self.my_variable: int = self.clref(3)
            print(self.my_variable) # will print 3
            self.cache["my_variable"] = 5
            print(self.my_variable) # will print 5

        Note that you can not pass this object on to another helper class. If you want
        to do that use self.cache.create_ref and create a global reference.

        :param default: The default value (if not existent in the cache yet)
        :param key_name: The key name in the cache, optional. By default the attribute
            name will be used
        :param create: Defines if the cache entry shall be stored if not existent yet
        """
        return CLRef(default_value=default, key_name=key_name, create=create)

    def __setattr__(self, key, value):
        """
        Overrides the default behavior so that if a CLRef is passed it will bind the
        attribute name to the corresponding cache entry and if a name of an already
        existing CLRef binding is passed will assign the value to the corresponding
        cache entry.

        :param key: The attribute key
        :param value: The new value
        """
        if "_bindings" not in self.__dict__:
            super().__setattr__(key, value)
            return
        cb = self._bindings.get(key, None)
        if isinstance(cb, CLRef):
            self.cache[cb._key_name] = value
            return
        if isinstance(value, CLRef):
            self._bindings[key] = value
            if value._key_name is None:
                value._key_name = key
            if value._init and value._key_name not in self.cache:
                self.cache[value._key_name] = value._default_value
            value._default_value = None
            return
        super().__setattr__(key, value)

    def __getattr__(self, item):
        """
        Overrides the default behavior so that if a cache binding was set up
        (see :meth:`clref`) the cache value is read instead of the attribute value.

        :param item: The key
        :return: The attribute's or cache element's value
        """

        if "_bindings" not in self.__dict__:
            return self.__dict__[item]
        cb = self._bindings.get(item, None)
        if isinstance(cb, CLRef):
            return self.__dict__["cache"][cb._key_name]
        return self.__dict__[item]
