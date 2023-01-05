"""
Implements :class:`LogBuilderRegistry` which keeps track of which LogBuilder is
currently active in which thread.
"""
from __future__ import annotations

import threading
from typing import Union

from scistag.common import StagLock
from scistag.vislog import LogBuilder


class LogBuilderRegistry:
    """
    Helper class which keeps track of which LogBuilder is currently active in which
    thread so it does not need to be passed to every log function.
    """

    _builder_access_lock = StagLock()
    """Global log to access shared builder data"""
    _builder_stack: dict[int, list["LogBuilder"]] = {}
    """Builder dictionary"""

    @classmethod
    def register_builder(cls, builder: "LogBuilder"):
        """
        Registers the builder which is currently building or updating

        :param builder: The builder
        """
        cur_thread = threading.get_ident()
        with cls._builder_access_lock:
            if cur_thread in cls._builder_stack:
                cls._builder_stack[cur_thread].append(builder)
            else:
                cls._builder_stack[cur_thread] = [builder]

    @classmethod
    def remove_builder(cls, builder: "LogBuilder"):
        """
        Removes the current builder from the registry

        :param builder: The assumed builder, for assertio only
        """
        cur_thread = threading.get_ident()
        with cls._builder_access_lock:
            assert cur_thread in cls._builder_stack
            stack: list = cls._builder_stack[cur_thread]
            assert stack.pop() == builder
            if len(stack) == 0:
                del cls._builder_stack[cur_thread]

    @classmethod
    def current_builder(cls) -> Union["LogBuilder", None]:
        """
        Returns the builder which is currently active in the local thread
        """
        cur_thread = threading.get_ident()
        with cls._builder_access_lock:
            if cur_thread not in cls._builder_stack:
                return None
            return cls._builder_stack[cur_thread][-1]
