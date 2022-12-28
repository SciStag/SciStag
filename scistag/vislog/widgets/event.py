"""
Implements the class :class:`VisualLogEvent` which defines the details of
an event to be processed by a VisualLog widget or the log itself.
"""

from dataclasses import dataclass

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import VisualLogBuilder
    from scistag.vislog.widgets.log_widget import LWidget


@dataclass
class LEvent:
    """
    Defines a single event raised by an interactive log page
    """

    widget: "LWidget"
    "The component which triggered the event"
    event_type: str
    "The type of the event"
    builder: Union["VisualLogBuilder", None] = None
    "The log builder which triggered the event"
    name: Union[str, None] = None
    "Name of the component which triggered the event"
