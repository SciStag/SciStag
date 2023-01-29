"""
Tests the widget class slider
"""
from scistag.vislog import VisualLog
from scistag.vislog.options import LSliderOptions
from scistag.vislog.widgets import LSlider, LValueChangedEvent
from .. import vl


def test_slider_embedding():
    """
    Tests the basic integration of a slider into a log
    """

    log = VisualLog(fixed_session_id="")
    svl = log.default_builder

    event_called: bool = False
    event_called_w_event: bool = False

    def event_handler():
        nonlocal event_called
        event_called = True

    def event_handler_with_event(event: LValueChangedEvent):
        nonlocal event_called_w_event
        event_called_w_event = True

    svl.test.checkpoint("addingSliders")

    hor_slider = svl.widget.slider(
        5, 4, 30, on_change=event_handler_with_event, value_bold=True
    )
    vert_slider = LSlider(
        vl,
        0.2,
        0.0,
        1.0,
        value_edit_field=False,
        vertical=True,
        on_change=event_handler,
    )
    zero_slider = LSlider(
        vl, 2.0, 2.0, 2.0, vertical=True, on_change=event_handler, show_value=False
    )
    options = LSliderOptions()
    options.show_value = "custom"
    options.vertical = True
    options.value_bold = True
    custom_value_slider = LSlider(
        vl, 2.0, 1.0, 5.0, on_change=event_handler, options=options
    )
    # vl.insert_backup(svl.create_backup())
    # vl.flush()
    svl.test.assert_cp_diff("e2b7933d0a6472037ff8b159557443fb", target=vl)
    assert vert_slider.get_value() == 0.2
    assert not event_called
    vert_slider.sync_value(0.2)
    assert not event_called
    vert_slider.sync_value(0.3)
    assert event_called
    assert not event_called_w_event
    hor_slider.sync_value(5)
    assert not event_called_w_event

    values = {hor_slider.identifier: 6}
    svl.page_session.update_values_js(svl.page_session.last_client_id, values)

    assert event_called_w_event
    zero_slider.sync_value(2.0)
