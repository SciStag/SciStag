"""
Defines TimeLogger which provides functions for timing the performance
and timestamp in a log.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union, Callable

from scistag.vislog.extensions.builder_extension import BuilderExtension
from scistag.vislog.extensions.time_measuring_context import TimeMeasuringContext

if TYPE_CHECKING:
    from scistag.vislog.log_builder import LogBuilder


class TimeLogger(BuilderExtension):
    """
    Helper class for logging time stamps and performance estimations to a log.
    """

    def __init__(self, builder: "LogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)
        self.show = self.__call__

    def __call__(self, prefix: str = "", postfix: str = "") -> LogBuilder:
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

    def measure(
        self,
        silent: bool = False,
        callback: Union[Callable, None] = None,
        prefix: str = "",
        postfix: str = "",
        br: bool = True,
    ) -> TimeMeasuringContext:
        """
        :param silent: Defines if nothing shall be logged but just the time measured
        :param callback: The callback to call after the measurement
        :param prefix: The prefix to be logged in front of the text
        :param postfix: The postfix to be logged after the text
        :param br: Defines if a linebreak shall be inserted after the logging
        """
        return TimeMeasuringContext(
            self.builder,
            start_time=time.time(),
            silent=silent,
            callback=callback,
            prefix=prefix,
            postfix=postfix,
            br=br,
        )
