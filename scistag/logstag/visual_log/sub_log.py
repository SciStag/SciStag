"""
Implements the class :class:`SubLog` which defines a log data area nested
within the main log of a :class:`VisualLog`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.logstag.visual_log.visual_log import VisualLog


@dataclass
class SubLog:
    """
    Defines a single entry on the log target stag
    """
    logs: dict
    "The log dictionaries for all targets"
    target: str
    "The target's name"
    max_fig_size: tuple[int, int]
    "The preview size of figures and images in pixels"
    log_limit: int = -1
    "The maximum count of log entries in this sub log"


class SubLogLock:
    """
    Automatically calls end_sub_log after leaving it's with block
    """

    def __init__(self, log: "VisualLog" | None):
        """
        :param log: The log to release
        """
        self.log = log
        "Defines the target log"
        self.valid = log is not None
        "Defines if the update shall be skipped"
        self.locked = False
        "Defines if the log has been locked yet"

    def __enter__(self) -> SubLogLock:
        if self.log and self.valid:
            self.locked = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.locked:
            self.log.end_sub_log()

    def __eq__(self, other):
        return self.valid == other

    def __ne__(self, other):
        return self.valid != other

    def __neg__(self):
        return not self.valid

    def __bool__(self):
        return self.valid
