"""
Implements the class :class:`LogButton` which allows the user to add an
interaction button to a log.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Union

from scistag.vislog.widgets.log_widget import LogWidget

if TYPE_CHECKING:
    from scistag.vislog.visual_log import VisualLog
    from scistag.vislog.log_event import LogEvent

CLICK_EVENT_TYPE = "click"
"Defines an event which is risen by a button click"


class LogButton(LogWidget):
    """
    The LogButton adds a button the log which upon click triggers it's
    click event.
    """

    def __init__(self,
                 log: "VisualLog",
                 name: str,
                 caption: str = "",
                 on_click: Callable | None = None
                 ):
        """
        :param log: The log to which the button shall be added
        :param name: The button's name
        :param caption: The button's caption
        :param on_click: The function to be called when the button is clicked
        """
        super().__init__(name=name, log=log)
        self.caption = caption
        "The buttons caption"
        from scistag.vislog.log_event import LogEvent
        self.on_click: Union[Callable[[LogEvent], None], None] = on_click

    def write(self):
        html = \
            f"""
            <input class="greenButton" type="button" value="{self.caption}" onclick="fetch('triggerEvent?name={self.name}&type={CLICK_EVENT_TYPE}')" />
            """
        self.log.default_builder.html(html)

    def handle_event(self, event: "LogEvent"):
        if event.event_type == CLICK_EVENT_TYPE:
            if self.on_click is not None:
                self.on_click(event)
            return
        super().handle_event(event)
