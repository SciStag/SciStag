"""
Implements the class :class:`LiveLogWidget` which is the base class for all
widgets which can be visualized within the live-area of a VisualLivelog.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.logstag.vislog import VisualLog
    from scistag.logstag.vislog.log_event import LogEvent


class LogWidget:
    """
    Defines a widget which can be attached to a VisualLiveLog
    """

    def __init__(self, log: "VisualLog", name: str):
        """
        :param log: The log to which this widget belongs
        :param name: The widget's name
        """
        self.name = name
        "The widget's name"
        self.log = log
        "The log to which this widget belongs"
        self.visible = True
        "Defines if the widget is currently visible"
        self.log.register_widget(name, self)

    def write(self):
        """
        Tells the widget to write all of it's data to the log
        """
        pass

    def handle_event(self, event: "LogEvent"):
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
