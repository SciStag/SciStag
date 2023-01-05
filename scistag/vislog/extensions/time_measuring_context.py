"""
Implements :class:`TimeMeasuringContext` which helps measuring the execution time of
specific time blocks.
"""

from __future__ import annotations

import time
from typing import Union, Callable

from scistag.vislog import LogBuilder


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
