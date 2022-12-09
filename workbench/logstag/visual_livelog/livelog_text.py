"""
Implements the class :class:`LiveLogText` which visualizes a dynamically
changeable text in a VisualLiveLog.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from scistag.vislog.widgets.log_widget import LWidget

if TYPE_CHECKING:
    from scistag.vislog import VisualLiveLog


class LText(LWidget):
    """
    Displays a text in the live log
    """

    def __init__(self, log: "VisualLiveLog", text: str | None):
        """
        :param text: The text to be set, parses as markdown.

            Text beginning with one or multiple hashtags (#) and a following
            space is considered a title. Otherwise the content is handled
            as text.
        """
        super().__init__(log)
        self.text = text

    def update(self, text: str):
        """
        Updates the widget's content

        :param text: The new text
        """
        if self.text == text:
            return
        self.text = text
        self.log.handle_widget_modified(self)

    def write(self):
        if self.text is not None:
            self.log.md(self.text)

    def __bool__(self):
        return super().__bool__() and self.text is not None
