"""
Implements the tests for the logstag module
"""

from scistag.tests.visual_test_log_scistag import VisualTestLogSciStag

test_log = VisualTestLogSciStag(test_filename=__file__,
                                formats_out={"html", "md", "txt"})
vl = test_log.default_builder


def teardown_module(_):
    """
    Finalize the test
    """
    test_log.finalize()
