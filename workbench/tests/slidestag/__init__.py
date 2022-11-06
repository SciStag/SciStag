"""
Implements the tests for the SlideStag module
"""
from scistag.common import ConfigStag

from .. import ensure_config

ensure_config()
skip_slidestag = ConfigStag.get("testConfig.SlideStag.skip", True)
