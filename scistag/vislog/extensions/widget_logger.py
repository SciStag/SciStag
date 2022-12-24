"""
Implements :class:`WidgetLogger` which helps adding interactive widgets such as buttons
or sliders to a log.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Union, Callable

from scistag.vislog.extensions.builder_extension import BuilderExtension
from scistag.vislog.widgets import LButton, LWidget, LEvent

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import VisualLogBuilder
    from scistag.vislog.widgets.timer import LTimer


class WidgetLogger(BuilderExtension):
    """
    Helps adding and managing dynamic and interactive components such as buttons
    or sliders
    """

    def __init__(self, builder: "VisualLogBuilder"):
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
        all_elements = self.page.cur_element.list_elements_recursive()
        for element in all_elements:
            if "widget" in element.element.flags:
                widget = element.element.flags["widget"]
                widgets[element.name] = widget
        return widgets

    def handle_event(self, event: "LEvent", widgets: dict[str, LWidget]):
        """
        Handles a single event and forwards it to the correct widget

        :param event: The event to be handled
        :param widgets: A dictionary of all known widgets
        """
        if event.name in widgets:
            widgets[event.name].handle_event(event)

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

    def button(
        self,
        name: str = "",
        caption: str = "",
        on_click: Union[Callable, None] = None,
    ) -> "LButton":
        """
        Adds a button to the log which can be clicked and raise a click event.

        :param name: The button's name
        :param caption: The button's caption
        :param on_click: The function to be called when the button is clicked
        :return: The button widget
        """
        from scistag.vislog.widgets.log_button import LButton

        new_button = LButton(self.builder, name, caption=caption, on_click=on_click)
        new_button.insert_into_page()
        return new_button

    def timer(
        self,
        interval_s: float | None = None,
        delays_s: float | None = None,
        on_tick: Union[Callable, None] = None,
        enforce: bool = False,
        name: str = "",
    ) -> "LTimer":
        """
        Adds a time to the log which is triggered in a defined interval

        :param interval_s: The timer's trigger interval in seconds
        :param delays_s: The delay before the initial tick is triggered in seconds
        :param enforce: Enforce the defined frequency if required to ensure a
            constant update rate. Note that your timer callback needs to be faster
            than the frequency, otherwise the system might end up in a sort of
            infinite loop.
        :param on_tick: The function to be called when the timer is triggered
        :param name: The timer's name
        :return: The timer widget
        """
        from scistag.vislog.widgets.timer import LTimer

        new_timer = LTimer(
            self.builder,
            name=name,
            on_tick=on_tick,
            interval_s=interval_s,
            delays_s=delays_s,
            enforce=enforce,
        )
        new_timer.insert_into_page()
        return new_timer
