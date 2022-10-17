"""
Integration of ImageStag tests
"""
from scistag.tests.visual_test_log_scistag import VisualTestLogSciStag

from scistag.common import ConfigStag
from ..config import ensure_config

ensure_config()
skip_imagestag = ConfigStag.get("testConfig.ImageStag.skip", False)

vl = VisualTestLogSciStag(test_filename=__file__)


def teardown_module(_):
    """
    Finalize the test
    """
    vl.finalize()
