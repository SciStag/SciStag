"""
CuteStag provides some basic helper interfaces to combine the strengths of
SciStag and Qt
"""

from __future__ import annotations

from scistag.common import StagLock

_cute_lock = StagLock()
"""
Thread-secure access lock
"""
_cute_module = None
"""
The Qt module if it could be loaded
"""
_loaded = False
"""
Defines if a loading approach was done
"""


def cute_available() -> bool:
    """
    Tries to load Qt and returns if it's available

    :return True if Qt is available
    """
    global _loaded, _cute_module
    with _cute_lock:
        if not _loaded:
            _loaded = True
            try:
                import PySide6

                _cute_module = PySide6
            except ModuleNotFoundError:
                pass
        return _cute_module is not None


def get_cute() -> object | None:
    """
    Returns the Qt module if it's available

    :return: The module (so far it's available)
    """
    if cute_available():
        return _cute_module
    else:
        return None
