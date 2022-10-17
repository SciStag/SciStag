"""
Contains the tests for the FileStag module
"""
from scistag.tests.visual_test_log_scistag import VisualTestLogSciStag

vl = VisualTestLogSciStag(test_filename=__file__)


def teardown_module(_):
    """
    Finalize the test
    """
    vl.finalize()
