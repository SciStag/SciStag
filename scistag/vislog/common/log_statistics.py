"""
Defines the class :class:`LogStatistics` which provides details about the
logs health and performance.
"""

from dataclasses import dataclass


@dataclass
class LogStatistics:
    """
    Provides information about the VisualLog's health and performance
    """

    update_rate: float
    "The current average update rate per second"
    update_counter: int
    "The total count of updates"
    uptime: float
    "The log's uptime in seconds"
