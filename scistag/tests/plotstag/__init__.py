"""
Tests for the PlotStag module
"""

from scistag.tests.visual_test_log_scistag import VisualTestLogSciStag

from ..config import ensure_config
from ...common import ConfigStag

ensure_config()
skip_plotstag = ConfigStag.get("testConfig.PlotStag.skip", False)

test_log = VisualTestLogSciStag(test_filename=__file__, )
vl = test_log.default_builder
vl.continuous_write = True


def teardown_module(_):
    """
    Finalize the test
    """
    test_log.finalize()
