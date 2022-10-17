"""
Implements the tests for the WebStag module
"""

from scistag.common import ConfigStag
from .. config import ensure_config

ensure_config()
skip_webstag = ConfigStag.get("testConfig.WebStag.skip", True)

