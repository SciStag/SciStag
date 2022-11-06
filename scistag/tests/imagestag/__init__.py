"""
Integration of ImageStag tests
"""
from scistag.tests.visual_test_log_scistag import VisualTestLogSciStag

from scistag.common import ConfigStag
from ..config import ensure_config

ensure_config()
skip_imagestag = ConfigStag.get("testConfig.ImageStag.skip", False)

test_log = VisualTestLogSciStag(test_filename=__file__)
vl = test_log.default_builder


def teardown_module(_):
    """
    Finalize the test
    """
    test_log.finalize()
