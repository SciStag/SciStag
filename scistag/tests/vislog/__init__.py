"""
Implements the tests for the vislog module
"""

from scistag.tests.visual_test_log_scistag import VisualTestLogSciStag

test_log = VisualTestLogSciStag(
    test_filename=__file__, formats_out={"html", "md", "txt"}, fixed_session_id=""
)
vl = test_log.default_builder


def teardown_module(_):
    """
    Finalize the test
    """
    test_log.finalize()
