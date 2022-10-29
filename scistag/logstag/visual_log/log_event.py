"""
Implements the class :class:`VisualLogEvent` which defines the details of
an event to be processed by a VisualLog widget or the log itself.
"""

from dataclasses import dataclass


@dataclass
class LogEvent:
    """
    Defines a single event raised by an interactive log page
    """

    name: str
    "Name of the component which triggered the event"
    event_type: str
    "The type of the event"
