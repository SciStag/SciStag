"""
Tests the log basic widgets
"""

from scistag.vislog import VisualLog
from scistag.vislog.widgets.log_event import LEvent
from scistag.vislog.widgets.log_button import LButton, CLICK_EVENT_TYPE


def test_widgets():
    """
    Tests interactive widgets
    """
    log = VisualLog()
    clicked = False

    def set_clicked():
        nonlocal clicked
        clicked = True

    button = log.default_builder.widget.add_button(
        "Abutton", "Click me", on_click=lambda event: set_clicked()
    )
    assert isinstance(button, LButton)
    log.default_builder.widget.add_event(
        LEvent(
            name=button.name,
            event_type=CLICK_EVENT_TYPE,
            builder=log.default_builder,
            widget=button,
        )
    )
    log.default_builder.widget.handle_event_list()
    assert clicked
