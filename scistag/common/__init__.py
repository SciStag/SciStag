import platform
from enum import IntEnum

from .cache import Cache, get_global_cache
from .cache_ref import CacheRef
from .component import Component
from .config_stag import ConfigStag
from .env import Env
from .essential_data import (
    ESSENTIAL_DATA_ARCHIVE_NAME,
    ESSENTIAL_DATA_URL,
    get_edp,
    ESSENTIAL_DATA_SIZE,
)
from .mt import StagLock
from .observer import DataObserver, DataObserverList
from .stag_app import StagApp
from .test_data import get_test_data, get_test_image, TestDataNames
from .sytem_info import SystemInfo

__version__ = "0.8.2"
"""The current release version"""

__all__ = [
    "ESSENTIAL_DATA_ARCHIVE_NAME",
    "ESSENTIAL_DATA_URL",
    "get_edp",
    "ESSENTIAL_DATA_SIZE",
    "Cache",
    "CacheRef",
    "StagApp",
    "Component",
    "ConfigStag",
    "get_test_data",
    "get_test_image",
    "TestDataNames",
    "StagLock",
    "Env",
    "get_global_cache",
    "DataObserver",
    "DataObserverList",
    "SystemInfo",
    "__version__",
]
