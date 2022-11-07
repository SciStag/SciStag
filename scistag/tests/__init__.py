import os.path

from scistag.common.test_data import TestConstants
from scistag.tests.config import ensure_config
from scistag.common import Env

__all__ = ["TestConstants", "ensure_config"]

# load preconfigured environment variables
Env.load_env_file(os.path.dirname(__file__) + "/.env", fail_silent=True)
