"""
Implements the class :class:`LiveLogWidget` which is the base class for all
widgets which can be visualized within the live-area of a VisualLivelog.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.logstag import VisualLiveLog


class LiveLogWidget:
    """
    Defines a widget which can be attached to a VisualLiveLog
    """

    def __init__(self, log: "VisualLiveLog"):
        """
        :param log: The log to which this widget belongs
        """
        self.log = log
        "The log to which this widget belongs"
        self.visible = True
        "Defines if the widget is currently visible"

    def write(self):
        """
        Tells the widget to write all of it's data to the log
        """
        pass

    def __bool__(self):
        """
        Defines if the widget is currently valid (has content)

        :return: True if the widget shall be displayed (and reserve a size slot)
        """
        return True
