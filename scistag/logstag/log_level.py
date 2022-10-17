"""
Implements the class :class:`LogLevel` which defines the importance of log
entries.
"""

from __future__ import annotations

import logging
from enum import IntEnum
from typing import Any


class LogLevel(IntEnum):
    """
    Enumeration of log levels
    """

    INFO = logging.INFO
    "Informational log output"
    DEBUG = logging.DEBUG
    "Developer log output"
    WARNING = logging.WARNING
    "Warnings - not critical yet though"
    ERROR = logging.ERROR
    "Serious error logs"
    CRITICAL = logging.CRITICAL
    "Really evil errors"

    def _missing_(cls, value: object) -> Any:
        if value == "info":
            return cls.INFO
        if value == "debug":
            return cls.DEBUG
        if value == "warning" or value == "warn":
            return cls.WARNING
        if value == "error":
            return cls.ERROR
        if value == "critical" or value == "fatal" or value == "uh oh":
            return cls.CRITICAL
