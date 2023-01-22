"""
Tests the time logging capabilities of the VisualTimeLogger helper class
"""
import time

from . import vl
from ...vislog import VisualLog


def test_time_logging_basics():
    """
    Tests the basic functions
    """
    test_log = VisualLog()
    test_log.default_builder.time.show()
    test_log.default_builder.time().flush()
    body = test_log.default_page.get_body("html")
    assert (
        b"-" in body
        and b":" in body
        and b"." in body
        and body.index(b".") > body.index(b":")
    )
    vl.embed(test_log.default_page)


def test_time_measuring():
    """
    Tests the time measuring context functionality
    """
    test_log = VisualLog()
    with test_log.default_builder.time.measure(prefix="Required "):
        test_log.default_builder.log("123")
    test_log.finalize()
    assert b"Required " in test_log.default_page.get_body("html")
    test_log = VisualLog()

    was_called = False

    def call_me(context):
        nonlocal was_called
        was_called = True

    with test_log.default_builder.time.measure(
        prefix="Required ", callback=call_me
    ) as mc:
        mc.start_time = time.time() - (65 * 60.0)
        test_log.default_builder.log("123")
    test_log.finalize()
    data = test_log.default_page.get_body("html")
    assert b"h " in data and b"m " in data

    test_log = VisualLog()
    with test_log.default_builder.time.measure(silent=True) as mc:
        pass
    test_log.finalize()
    data = test_log.default_page.get_body("html")
    assert len(data) == 0
