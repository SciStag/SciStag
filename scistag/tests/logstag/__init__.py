"""
Implements the tests for the logstag module
"""

from scistag.tests.visual_test_log_scistag import VisualTestLogSciStag

vl = VisualTestLogSciStag(test_filename=__file__,
                          formats_out={"html", "md", "txt"})


def teardown_module(_):
    """
    Finalize the test
    """
    vl.finalize()
