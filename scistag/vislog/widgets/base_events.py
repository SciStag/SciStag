"""
Implements common, not widget-specific base events
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Union

from scistag.vislog.widgets.event import LEvent

if TYPE_CHECKING:
    from scistag.vislog.widgets.log_widget import LWidget

VALUE_CHANGE_EVENT_TYPE = "widget_value_change"
"Defines an event which is risen by a value change, e.g. of a slider or a combo box"


class LValueChangedEvent(LEvent):
    """
    An event which is triggered when the value of an object changed
    """

    def __init__(self, widget: "LWidget", value, **params):
        """
        :param widget: The widget such as a LButton which was modified
        :param value: The new value
        :param params: Additional parameters
        """
        super().__init__(event_type=VALUE_CHANGE_EVENT_TYPE, widget=widget, **params)
        self.value = value

    value: int | float | str | bool
    """The widget's new value"""


LValueChangedCallable = Union[Callable[[LValueChangedEvent], None], Callable]
"""Callable which is called when a value changed event is triggerd"""
