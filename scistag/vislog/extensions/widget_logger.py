"""
Implements :class:`WidgetLogger` which helps adding interactive widgets such as buttons
or sliders to a log.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union, Callable

from scistag.vislog.widgets import LWidget, LEvent
from scistag.vislog.extensions.builder_extension import BuilderExtension
from scistag.vislog.widgets.timer import LTimer
from scistag.vislog.widgets.button import CLICK_EVENT_TYPE, LClickEvent

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import LogBuilder
    from scistag.vislog.widgets import LButton
    from scistag.vislog.widgets import LSlider, LFileUpload


class WidgetLogger(BuilderExtension):
    """
    Helps adding and managing dynamic and interactive components such as buttons
    or sliders
    """

    def __init__(self, builder: "LogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)
        self._events = []
        "List of unhandled events"

    def add_event(self, event: "LEvent"):
        """
        Adds an event to the event queue which will be handled before and
        after the next re-build (or loop turn in case of a continuous log).

        :param event: The new event
        """
        self._events.append(event)

    def handle_event_list(self) -> float | None:
        """
        Handles all queued events and clears the event queue

        :return: The timestamp when the next event is awaited
        """
        event_list = self._events
        self._events = []
        widgets = self.find_all_widgets()
        next_execution = None
        for widget in widgets.values():
            widget: LWidget
            next_event = widget.handle_loop()
            if next_event is not None:
                if next_execution is None or next_event < next_execution:
                    next_execution = next_event
        for element in event_list:
            self.handle_event(element, widgets)
        return next_execution

    def find_all_widgets(self) -> dict[str, LWidget]:
        """
        Returns a dictionary of all known widgets by scanning the element tree

        :return: A list of all widgets
        """
        widgets: dict[str, LWidget] = {}
        all_elements = self.page_session.cur_element.list_elements_recursive()
        for element in all_elements:
            if "widget" in element.element.flags:
                widget: LWidget = element.element.flags["widget"]
                widgets[element.name] = widget
        return widgets

    def handle_event(self, event: "LEvent", widgets: dict[str, LWidget]) -> bool:
        """
        Handles a single event and forwards it to the correct widget

        :param event: The event to be handled
        :param widgets: A dictionary of all known widgets
        :return: True if the widget could be found
        """
        if event.name in widgets:
            widgets[event.name].handle_event(event)
            return True
        return False

    def get_events(self, clear: bool = False) -> list["LEvent"]:
        """
        Returns the current list of events

        :param clear: Defines if all events shall be removed afterwards
        :return: The event list
        """
        event_list = list(self._events)
        if clear:
            self._events = []
        return event_list

    def button(self, *args, **kwargs) -> "LButton":
        """
        Adds a button to the log which can be clicked and raise a click event.

        For further details see :class:`LButton`.
        """
        from scistag.vislog.widgets.button import LButton

        new_button = LButton(self.builder, *args, **kwargs)
        return new_button

    def slider(
        self,
        *args,
        **kwargs,
    ) -> "LSlider":
        """
        Adds a value slider to the log.

        For further details see :class:`LSlider`
        """
        from scistag.vislog.widgets.slider import LSlider

        new_slider = LSlider(self.builder, *args, **kwargs)
        return new_slider

    def timer(
        self,
        *args,
        **kwargs,
    ) -> "LTimer":
        """
        Adds a timer to the log which is triggered in a defined interval

        For further details see :class:`LTimer`
        """
        from scistag.vislog.widgets.timer import LTimer

        new_timer = LTimer(self.builder, *args, **kwargs)
        return new_timer

    def file_upload(
        self,
        *args,
        **kwargs,
    ) -> "LFileUpload":
        """
        Adds a file upload widget to the log

        For further details see :class:`LFileUpload`
        """
        from scistag.vislog.widgets import LFileUpload

        new_widget = LFileUpload(self.builder, *args, **kwargs)
        return new_widget

    def handle_client_event(self, **params):
        """
        Handles a client event (sent from JavaScript)

        :param params: The event parameters
        """
        event_type = params.pop("type", "")
        widget_name = params.pop("name", "")
        all_widgets = self.find_all_widgets()
        if widget_name in all_widgets:
            widget = all_widgets[widget_name]
            if event_type == CLICK_EVENT_TYPE:
                widget.raise_event(LClickEvent(widget=widget))

    def sync_values(self, values: dict):
        """
        Updates all widget values to the modified value provided by the client and
        triggers the associated events.

        :param values: Internal widget mame, Value Pairs
        """
        if len(values):
            all_widgets = self.find_all_widgets()
            for key, value in values.items():
                if key in all_widgets:
                    widget: LWidget = all_widgets[key]
                    cur_value = widget.get_value()
                    if cur_value is None:
                        continue
                    widget.sync_value(value)
                    self.builder.page_session.update_last_user_interaction()
