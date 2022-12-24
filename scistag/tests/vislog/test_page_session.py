"""
Tests the PageSession class
"""
import time

import pytest

from scistag.vislog import VisualLog
from scistag.vislog.common.log_element import LogElement


def test_page_session_backup():
    """
    Tests the backup function
    """
    log = VisualLog()
    vl = log.default_builder
    vp = log.default_page
    vl.log("Test")
    vp.begin_update()
    vp.begin_update()
    vl.log("HelloWorld")
    lock, re = vp.get_root_element()
    re: LogElement
    assert b"HelloWorld" not in re.build("html")
    assert (
        b"HelloWorld" not in vp.render_element(name="vlbody", output_format="html")[1]
    )
    assert lock is vp._backup_lock
    lock, re = vp.get_root_element(backup=False)
    assert lock is vp._page_lock
    assert b"HelloWorld" in re.build("html")
    vp.end_update()
    vp.end_update()
    assert b"HelloWorld" in re.build("html")
    assert b"HelloWorld" in vp.render_element(name="vlbody", output_format="html")[1]


def test_rendering():
    """
    Tests the rendering capability
    """
    log = VisualLog()
    vl = log.default_builder
    vp = log.default_page
    assert vp.render_element("nonsense") == (0.0, b"")
    assert vp.render_element("") == (0.0, b"")
    assert vp.render_element("vlbody.subelemenet") == (0.0, b"")
    assert vp.render_element(name=None)[0] != 0
    vp.begin_sub_element("subelement")
    vl.log("Hello world")
    vp.end_sub_element()
    assert b"Hello world" in vp.render_element("vlbody.subelement")[1]
    with pytest.raises(RuntimeError):
        vp.end_sub_element()


def test_events():
    """
    Tests the event handling capability
    """
    log = VisualLog()
    vl = log.default_builder
    vp = log.default_page
    vp.get_events_js("12345")
    vp.get_events_js("12345")
    assert vp.last_client_id == "12345"
    last_time = vp.element_update_times["vlbody"]
    vp.reset_client()
    vp.get_events_js("4567")
    assert (
        b"Session was opened in another browser or tab." in vp.get_events_js("12345")[1]
    )
    vl.log("1234")
    time.sleep(1.0 / 15)
    vp.get_events_js("4567")
    assert last_time != vp.element_update_times["vlbody"]
    last_time = vp.element_update_times["vlbody"]
    vp.begin_sub_element("subelement")
    vl.log("Hello world")
    vp.end_sub_element()
    time.sleep(1.0 / 15)
    vp.get_events_js("4567")
    assert last_time != vp.element_update_times["vlbody"]
