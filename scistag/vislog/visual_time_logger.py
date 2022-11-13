"""
Defines VisualLogTimeLogger which provides functions for timing the performance
and timestamp in a log.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Union, Callable

import numpy as np
from pandas import DataFrame, Series
from scistag.vislog.visual_log_element_context import \
    VisualLogElementContext

from scistag.imagestag import Image
from scistag.plotstag import Figure

if TYPE_CHECKING:
    from .visual_log_builder import VisualLogBuilder


class VisualLogTimeLogger:
    """
    Helper class for logging time stamps and performance estimations to a log.
    """

    def __init__(self, builder: "VisualLogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        self.builder: "VisualLogBuilder" = builder
        self._log = self.builder.target_log
        self.log = self.__call__

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
