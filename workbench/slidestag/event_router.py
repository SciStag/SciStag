from __future__ import annotations
from .base_events import TapEvent, MouseButton
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.slidestag.slide_session import SlideSession
    from scistag.slidestag.widget import Widget


class EventRouter:
    """
    Manages the handling of user events from remote devices or the SDK solution
    hosting the Slide's view
    """

    def __init__(self, slide_session: SlideSession):
        """
        :param slide_session: The session this router manages
        """
        self._mouse_focus: Widget | None = None
        self._session = slide_session

    def handle_mouse_event(self, root_window, event):
        """
        Handles the next mouse event

        :param root_window: The root window
        :param event: The event
        """
        coordinate = event["coord"]
        target = root_window.get_relative_coordinate(coordinate)
        if event['type'] == "mouseDown" and target is not None:
            self._mouse_focus = target[0]
        elif event['type'] == "mouseUp":
            if self._mouse_focus is not None and self._mouse_focus == target[0]:
                click_event = TapEvent(self._mouse_focus,
                                       coordinate=(target[1], target[2]),
                                       coordinate_absolute=(
                                       coordinate[0], coordinate[1]),
                                       button=MouseButton.LEFT)
                self._mouse_focus.handle_click(click_event)
            self._mouse_focus = None

    def handle_raw_events(self, events):
        """
        Handles the raw events provided by a remote client or embedding solution
        such as the browser or a remote tablet providing the events.

        :param events: A list of events in the JSON format
        * "mouseDown" / "tapDown" + "coord" in pixels relative to the main window
        * "mouseUp" / "tapUp" + "coord" in pixels relative to the main window
        * "mouseMove" / "tapMove" + "coord" in pixels relative to the main window
        """
        root_window: Widget = self._session.get_root_window()
        new_events = []
        for element in events:
            relative = element.get('relative', False)
            if relative:
                width, height = root_window.size.to_int_tuple()
                coordinate = element["coord"][0] * width, \
                             element["coord"][1] * height
                element["coord"] = coordinate
            if element["type"] == "tapMove":
                element["type"] = "mouseMove"
            if element["type"] == "tapDown":
                element["type"] = "mouseDown"
            if element["type"] == "tapUp":
                element["type"] = "mouseUp"
            new_events.append(element)

        events = new_events
        for event in events:
            if "coord" in event and root_window is not None:
                self.handle_mouse_event(root_window, event)
