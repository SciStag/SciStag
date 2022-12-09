"""
Tests the log basic widgets
"""

from scistag.vislog import VisualLog
from scistag.vislog.widgets.log_event import LogEvent
from scistag.vislog.widgets.log_button import LogButton, CLICK_EVENT_TYPE


def test_widgets():
    """
    Tests interactive widgets
    """
    log = VisualLog()
    clicked = False

    def set_clicked():
        nonlocal clicked
        clicked = True

    button = log.add_button("Abutton", "Click me",
                            on_click=lambda event: set_clicked())
    assert isinstance(button, LogButton)
    log.add_event(LogEvent("Abutton", CLICK_EVENT_TYPE))
    log.handle_event_list()
    assert clicked
