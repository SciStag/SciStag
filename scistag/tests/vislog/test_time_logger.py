"""
Tests the time logging capabilities of the VisualTimeLogger helper class
"""

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
