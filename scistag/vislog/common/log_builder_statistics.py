"""
Defines statistics about a LogBuilder
"""

from __future__ import annotations


class LogBuilderStatistics:
    """
    Contains statistics about the log
    """

    build_counter: int = 0
    """
    How often was the log build?
    """
    last_build_time_s: float = 0.0
    """
    The amount of time in seconds for the last build execution
    """
    total_build_time_s: float = 0.0
    """
    The total build time in seconds
    """
