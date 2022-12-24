"""
Implements the class :class:`LiveLogWidget` which is the base class for all
widgets which can be visualized within the live-area of a VisualLivelog.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from scistag.vislog.common.log_element import LogElement

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import VisualLogBuilder
    from scistag.vislog.widgets.log_event import LEvent


class LWidget:
    """
    Defines a widget which can be attached to a VisualLiveLog
    """

    def __init__(
        self,
        builder: "VisualLogBuilder",
        name: str,
        is_view: bool = True,
        explicit_name: str | None = None,
    ):
        """
        :param builder: The log to which this widget belongs
        :param name: The widget's name
        :param is_view: Defines if the widget is a view / a UI component
        :param explicit_name: The (absolute) name to be assigned to the widget
        """
        if len(name) == 0:
            name = self.__class__.__qualname__
        self.name = name
        "The widget's name"
        self.builder = builder
        "The log builder"
        self.log = self.builder.target_log
        "The log to which this widget belongs"
        self.page_session = self.builder.page_session
        "The page to which we are logging"
        self.visible = True
        "Defines if the widget is currently visible"
        self.is_view = is_view
        "Defines if the widget is a UI component"
        name = (
            self.builder.page_session.reserve_unique_name(self.name, digits=4)
            if explicit_name is None
            else explicit_name
        )
        self.name = name
        self.sub_element = self.builder.page_session.cur_element.add_sub_element(
            name=name
        )
        self.sub_element.flags["widget"] = self

    def insert_into_page(self):
        """
        Inserts the widget into the page
        """
        if not self.is_view:
            return
        self.builder.page_session.enter_element(self.sub_element)
        self.write()
        self.builder.page_session.end_sub_element()

    def write(self):
        """
        Tells the widget to write all of its data to the log
        """

    def handle_event(self, event: "LEvent"):
        """
        Is called for each event received by the web server
        """
        raise NotImplementedError("Not implemented")

    def __bool__(self):
        """
        Defines if the widget is currently valid (has content)

        :return: True if the widget shall be displayed (and reserve a size slot)
        """
        return True

    def handle_loop(self) -> float | None:
        """
        This method is called automatically for every registered widget when ever
        the session's main loop is run.

        :return: The timestamp when the next event is scheduled.
        """
        return None

    def raise_event(self, event: LEvent):
        """
        Raises an event and triggers the event handler

        :param event: The event to be triggered and handled
        """
        self.handle_event(event)
