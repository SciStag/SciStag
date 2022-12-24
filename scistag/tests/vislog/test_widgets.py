"""
Tests the log basic widgets
"""
from scistag.common.time import sleep_min
from scistag.vislog import VisualLog
from scistag.vislog.widgets.log_event import LEvent
from scistag.vislog.widgets.log_button import LButton, CLICK_EVENT_TYPE
from scistag.vislog.widgets.timer import LTimer


def test_widgets():
    """
    Tests interactive widgets
    """
    log = VisualLog()
    clicked = False

    def set_clicked():
        nonlocal clicked
        clicked = True

    button = log.default_builder.widget.button(
        name="Abutton", caption="Click me", on_click=lambda event: set_clicked()
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

    called = False

    def ticked():
        nonlocal called
        called = True

    timer = log.default_builder.widget.timer(interval_s=0.05, on_tick=ticked)
    sleep_min(0.1)
    assert isinstance(timer, LTimer)
    log.handle_page_events()
    assert called

    assert timer
    timer.insert_into_page()  # should do just nothing

    timer = LTimer(name="", builder=log.default_builder)
    assert "LTimer" in timer.name
