"""
Tests the PageSession class
"""
import time
from unittest import mock

import pytest
import random

from scistag.common.time import sleep_min
from scistag.logstag.console_stag import Console
from scistag.vislog import VisualLog
from scistag.vislog.common.log_element import LogElement
from scistag.vislog.sessions.page_session import PageSession, create_unique_session_id
from scistag.vislog.widgets.button import CLICK_EVENT_TYPE
from scistag.webstag.server import WebRequest


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
    sleep_min(1.0 / 15)
    vp.get_events_js("4567")
    assert (
        b"Session was opened in another browser or tab." in vp.get_events_js("12345")[1]
    )
    vl.log("1234")
    sleep_min(1.0 / 15)
    vp.get_events_js("4567")
    assert last_time != vp.element_update_times["vlbody"]
    last_time = vp.element_update_times["vlbody"]
    sleep_min(1.0 / 15)
    vp.begin_sub_element("subelement")
    vl.log("Hello world")
    vp.end_sub_element()
    sleep_min(1.0 / 15)
    vp.get_events_js("4567")
    assert last_time != vp.element_update_times["vlbody"]

    dummy_page = PageSession(builder=vp.builder, options=vl.options)
    vp._set_redirect_event_receiver(dummy_page)
    vp.handle_events()

    he_mock_result = 123.4
    ne_mock_result = None

    def he_mock():
        return he_mock_result

    def ne_mock():
        return ne_mock_result

    with (
        mock.patch.object(dummy_page, "handle_events", he_mock),
        mock.patch.object(vp.builder.widget, "handle_event_list", ne_mock),
    ):
        assert vp.handle_events() == 123.4
        ne_mock_result = 100.0
        assert vp.handle_events() == 100.0
        ne_mock_result = 200.0
        assert vp.handle_events() == 123.4
    vp.get_events_js(vp.last_client_id)
    vp.update_values_js(vp.last_client_id, {})
    vp.update_values_js(vp.last_client_id, {"notExiting": ""})
    test_button = vl.widget.button()
    vp.update_values_js(vp.last_client_id, {test_button.identifier: "123"})
    vp.handle_client_event(type=CLICK_EVENT_TYPE, name=test_button.identifier)
    vp.handle_client_event(type="widget_not_existing", name=test_button.identifier)
    vp.handle_client_event(type=CLICK_EVENT_TYPE, name="not_existing")
    vp.update_values_js("newClientId", {})


def test_session_id():
    """
    Tests the creation of unique session ids
    """

    counter = 0

    def rand_int_repl(start, end):
        nonlocal counter
        if end == 255:
            return 0
        counter += 1
        return counter

    session_list = set()
    with mock.patch("random.randint", rand_int_repl) as pmock:
        cur_id = create_unique_session_id()
        assert cur_id not in session_list
        cur_id = create_unique_session_id()
        assert cur_id not in session_list
        session_list.add(cur_id)


def test_write_data():
    """
    Tests .write_data
    """
    log = VisualLog()
    assert log.default_page.write_data("html", b"Hello")
    assert not log.default_page.write_data("pdf", b"Hello")


def test_writing_methods():
    """
    Tests  the different writing methods
    """
    options = VisualLog.setup_options()
    options.output.setup(formats={"html", "md", "console"})
    log = VisualLog(options=options)
    page = log.default_page
    page.write_md("**Hello**")
    page.write_md(b"how are you")
    content = page.render_element(output_format="md")[1]
    assert b"Hello" in content and b"how are" in content
    page._add_to_console("hello")
    console = Console()
    prog_console = Console()
    prog_console.progressive = True
    page.add_console(console)
    page.add_console(prog_console)
    content = page.render_element(output_format="console")[1]
    assert b"hello" in content
    assert page.render() is page
    page.write_to_disk(formats={"html"})


def test_web_request():
    """
    Tests if a web request can be handled
    """
    request = WebRequest()
    request.path = "live"
    options = VisualLog.setup_options()
    log = VisualLog(options=options)
    page = log.default_page
    result = page.handle_web_request(request)
    assert result is not None
    assert result.status == 200


def test_index_name():
    """
    Tests receiving the index names
    """
    options = VisualLog.setup_options()
    options.output.setup(formats={"html", "md", "console"}, index_name="test")
    log = VisualLog(options=options)
    page = log.default_page
    assert page.get_index_name("txt") == "test.txt"
    assert page.get_index_name("md") == "test.md"
    assert page.get_index_name("html") == "test.html"
    assert page.get_index_name("console") is None
