import platform

from .essential_data import ESSENTIAL_DATA_ARCHIVE_NAME, ESSENTIAL_DATA_URL, \
    get_edp, ESSENTIAL_DATA_SIZE
from .mt import StagLock
from .cache import Cache, get_global_cache
from .component import Component
from .config_stag import ConfigStag
from .test_data import get_test_data, get_test_image, TestDataNames
from .env import Env
from .observer import Observer, ObserverList

WINDOWS = ("CYGWIN" in platform.system().upper() or
           "WINDOWS" in platform.system().upper())
"Defines if we are using Windows"

__all__ = ["ESSENTIAL_DATA_ARCHIVE_NAME", "ESSENTIAL_DATA_URL", "get_edp",
           "ESSENTIAL_DATA_SIZE",
           "Cache",
           "Component", "ConfigStag",
           "get_test_data", "get_test_image", "TestDataNames",
           "StagLock", "Env", "WINDOWS", "get_global_cache",
           "Observer", "ObserverList"]
