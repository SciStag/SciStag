"""
Implements the base events for the SlideStag module
"""
from typing import Callable


class WidgetEvent(dict):
    """
    The event base class for Widget events
    """

    def __init__(self, widget):
        """
        :param widget: The widget which was originally targeted by the event
        """
        super().__init__()
        self.widget = widget
        "The widget which triggered the event"
        self.suppress_low_level_event = False
        "Defines if the low level standard action shall be skipped"


class WidgetEventHandler:
    """
    Defines the handler for a single event type
    """

    def __init__(self, event_class: type):
        """
        Handles the events posted to a given event

        :param event_class: The event class of this event handler
        """
        self.event_class = event_class
        self._listeners: list[Callable[[event_class], bool]] = []

    def execute(self, event: WidgetEvent) -> bool:
        """
        Broadcasts the event ot all listeners

        :param event: The event to be executed
        :return: False if the root event shall not be executed
        """
        for element in self._listeners:
            result = element(event)
            if not result:
                return False
        return True

    def add(self, callback_function: Callable[[WidgetEvent], bool]):
        """
        Adds a function be called when the event is triggered

        :param callback_function: A callback function receiving the event.
            If it returns false the base event handle is not executed.
        """
        self._listeners.append(callback_function)

    def remove(self, callback_function: Callable[[WidgetEvent], bool]):
        """
        Removes an event handler

        :param callback_function: A callback function to be removed.
        """
        self._listeners.remove(callback_function)
