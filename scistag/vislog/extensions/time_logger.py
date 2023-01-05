"""
Defines TimeLogger which provides functions for timing the performance
and timestamp in a log.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union, Callable

from scistag.vislog.extensions.builder_extension import BuilderExtension

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import LogBuilder


class TimeMeasuringContext:
    """
    A context which will automatically log the passed time a log once it's context
    is left.
    """

    def __init__(
        self,
        builder: "LogBuilder",
        start_time: float,
        silent: bool = False,
        callback: Union[Callable, None] = None,
        prefix: str = "",
        postfix: str = "",
        br: bool = True,
    ):
        """
        :param builder: The build to which we shall log after the measurement
        :param start_time: The start time
        :param silent: Defines if nothing shall be logged but just the time measured
        :param callback: The callback to call after the measurement
        :param prefix: The prefix to be logged in front of the text
        :param postfix: The postfix to be logged after the text
        :param br: Defines if a linebreak shall be inserted after the logging
        """
        self.builder = builder
        """The builder to which we shall log"""
        self.silent: bool = silent
        """Defines if nothing shall be logged but just the time measured"""
        self.start_time = start_time
        """The sart time"""
        self.prefix = prefix
        """Text to be logged before the time result"""
        self.postfix = postfix
        """Text to be logged after the time result"""
        self.time_passed: float = 0.0
        """The time passed in seconds while the context was active"""
        self.br: bool = br
        """Defines if a linebreak shall be logged after the text"""
        self.callback = callback
        """Callback to be called with this object being passed as argument"""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        time_diff = time.time() - self.start_time
        self.time_passed = time_diff
        if self.callback is not None:
            self.callback(self)
        if self.silent:
            return
        seconds = time_diff
        minutes = int(seconds / 60)
        hours = minutes // 60
        result = self.prefix
        if hours > 0:
            minutes -= hours * 60
            result += f"{hours:0.2f}h "
        if minutes > 0:
            seconds -= minutes * 60
            result += f"{minutes:0.2f}m "
        result += f"{seconds:0.2f}s"
        result += self.postfix
        self.builder.text(result, br=self.br)


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
