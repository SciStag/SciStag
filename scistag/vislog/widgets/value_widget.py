"""
Defined the class LValueWidget - the base widget class for widgets which store a single
value such as an edit field or a combo box (select).
"""

from __future__ import annotations

from typing import Any, Union

from scistag.vislog import LogBuilder
from scistag.vislog.widgets.log_widget import LWidget
from scistag.vislog.widgets.base_events import (
    LValueChangedCallable,
    LValueChangedEvent,
    LEvent,
)

LValueWidgetTypes = Union[int, float, str, bool]
"""Types supported as value for a LValueWidget"""


class LValueWidget(LWidget):
    """
    The LValueWidget class defines a widget which stores a single data value and
    can change a single value such as a slider, a checkbox or a text field.

    The value has to be in a JSON compatible format, e.g. int, float, string or bool
    """

    def __init__(
        self,
        builder: LogBuilder,
        value: LValueWidgetTypes,
        name: str | None = None,
        on_change: Union[LValueChangedCallable, None] = None,
        target: str | None = None,
        html_class: Union[str, None] = None,
        html_style: Union[str, None] = None,
        **kwargs,
    ):
        """
        :param builder: The builder object
        :param value: The initial value
        :param name: The widget's name
        :param on_change: Called when ever the element's value was modified
        :param target: Cache target key. If defined all updates to the widget's value
            will be stored in the cache variable defined
        :param html_class: The html class to be used
        :param html_style: Additional style flags
        :param kwargs: Additional keyword arguments
        """
        super().__init__(
            builder=builder,
            name=name,
            html_class=html_class,
            html_style=html_style,
            **kwargs,
        )
        self._value: LValueWidgetTypes = value
        """The element's value"""
        self.on_change: LValueChangedCallable = on_change
        """The event to be called when the widget's value was modified"""
        self.target = target
        """Name of the cache variable in which updates shall be stored"""

    def handle_event(self, event: LEvent):
        if isinstance(event, LValueChangedEvent):
            if self.target is not None:
                self.builder.cache.set(self.target, event.value, keep=True)
            self.call_event_handler(self.on_change, event)
        super().handle_event(event)

    @property
    def value(self) -> LValueWidgetTypes:
        """
        Returns the widgets current value
        """
        return self._value

    def get_value(self) -> LValueWidgetTypes:
        """
        Returns the element's value

        :return: The current value
        """
        return self._value

    def sync_value(self, new_value: Any, trigger_event: bool = True):
        """
        Updates the value and triggers all related events

        :param new_value: The new value
        :param trigger_event: Defines if an event may be triggered
        """
        if self._value == new_value:
            return
        self._value = new_value
        if self.target is not None:
            self.builder.cache.set(self.target, new_value, keep=True)
        if trigger_event:
            change_event = LValueChangedEvent(widget=self, value=new_value)
            self.raise_event(change_event)
