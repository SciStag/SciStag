"""
Defines TimeLogger which provides functions for timing the performance
and timestamp in a log.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Union, Callable

from scistag.vislog.extensions.builder_extension import BuilderExtension

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import VisualLogBuilder


class TimeLogger(BuilderExtension):
    """
    Helper class for logging time stamps and performance estimations to a log.
    """

    def __init__(self, builder: "VisualLogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)
        self.show = self.__call__

    def __call__(self, prefix: str = "", postfix: str = "") -> VisualLogBuilder:
        """
        Logs a timestamp to the log

        :param prefix: The text before the timestamp
        :param postfix: The text after the timestamp
        :return: The builder
        """
        from datetime import datetime

        dt_object = datetime.now()
        cur_time = f"{str(dt_object.date())} {str(dt_object.time())}"
        elements = [cur_time]
        if len(prefix) > 0:
            elements.insert(0, prefix)
        if len(postfix) > 0:
            elements.append(postfix)
        self.builder.log("".join(elements))
        return self.builder
