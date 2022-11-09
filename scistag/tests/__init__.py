import os.path

from scistag.common.test_data import TestConstants
from scistag.tests.config import ensure_config
from scistag.common import Env

# load preconfigured environment variables
Env.load_env_file(os.path.dirname(__file__) + "/.env", fail_silent=True)

RELEASE_TEST = os.environ.get("SCISTAG_FULL_TEST", "0") == "1"
"""
Set to true if a full test shall be executed including long running and
resource intensive regression tests.
"""

__all__ = ["TestConstants", "ensure_config", "RELEASE_TEST"]
