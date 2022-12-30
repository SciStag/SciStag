"""
Implements the class :class:`LButton` which allows the user to add an
interaction button to a log.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Union

from scistag.vislog.widgets.log_widget import LWidget
from scistag.vislog.widgets.event import LEvent

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import LogBuilder

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
        builder: "LogBuilder",
        name: str = "button",
        caption: str = "",
        on_click: Union[Callable, None] = None,
        insert: bool = True,
    ):
        """
        :param builder: The log builder to which the button shall be added
        :param name: The button's name
        :param caption: The button's caption
        :param on_click: The function to be called when the button is clicked
        :param insert: Defines if the element shall be inserted into the log

        """
        super().__init__(name=name, builder=builder)
        self.caption = caption
        "The buttons caption"
        from scistag.vislog.widgets.event import LEvent

        self.on_click: Union[Callable, None] = on_click
        "The function to be called when the button is clicked"
        if insert:
            self.insert_into_page()

    def write(self):
        html = f"""
            <input class="greenButton" type="button" value="{self.caption}" onclick="fetch('triggerEvent?name={self.identifier}&type={CLICK_EVENT_TYPE}')" />
            """
        self.builder.html(html)

    def handle_event(self, event: "LEvent"):
        if event.event_type == CLICK_EVENT_TYPE:
            self.call_event_handler(self.on_click, event)
            self.page_session.update_last_user_interaction()
            return
        super().handle_event(event)
