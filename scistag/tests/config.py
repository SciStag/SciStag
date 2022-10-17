"""
Initializes the unit test configuration
"""

import os.path
from threading import RLock
from scistag.common import ConfigStag

access_lock = RLock()
config_loaded = False


def ensure_config():
    """
    Prepares unit test base variables
    """
    global config_loaded
    with access_lock:
        if not config_loaded:
            bp = os.path.dirname(__file__)
            ConfigStag.load_config_file(bp + "/test_config.json", environment="SC_", required=False)
            config_loaded = True


ensure_config()
