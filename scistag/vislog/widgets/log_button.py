"""
Implements the class :class:`LButton` which allows the user to add an
interaction button to a log.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Union

from scistag.vislog.widgets.log_widget import LWidget
from scistag.vislog.widgets.log_event import LEvent

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import VisualLogBuilder

CLICK_EVENT_TYPE = "widget_click"
"Defines an event which is risen by a button click"


class LClickEvent(LEvent):
    """
    A click event which is triggered when a widget was clicked
    """

    def __init__(self, widget: LWidget, **params):
        """
        :param widget: The widget such as a LButton which was clicked
        :param params: Additional parameters
        """
        super().__init__(event_type=CLICK_EVENT_TYPE, widget=widget, **params)


class LButton(LWidget):
    """
    The LButton adds a button the log which upon click triggers it's
    click event.
    """

    def __init__(
        self,
        builder: "VisualLogBuilder",
        name: str,
        caption: str = "",
        on_click: Callable | None = None,
    ):
        """
        :param builder: The log builder to which the button shall be added
        :param name: The button's name
        :param caption: The button's caption
        :param on_click: The function to be called when the button is clicked
        """
        super().__init__(name=name, builder=builder)
        self.caption = caption
        "The buttons caption"
        from scistag.vislog.widgets.log_event import LEvent

        self.on_click: Union[Callable, None] = on_click
        "The function to be called when the button is clicked"

    def write(self):
        html = f"""
            <input class="greenButton" type="button" value="{self.caption}" onclick="fetch('triggerEvent?name={self.name}&type={CLICK_EVENT_TYPE}')" />
            """
        self.builder.html(html)

    def handle_event(self, event: "LEvent"):
        if event.event_type == CLICK_EVENT_TYPE:
            if self.on_click is not None:
                self.on_click()
            return
        super().handle_event(event)
