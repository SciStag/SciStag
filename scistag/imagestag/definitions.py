"""
Defines the common definitions required by all major components of the ImageStag
module.
"""

from __future__ import annotations
import enum
import importlib
from multiprocessing import RLock
from types import ModuleType
from typing import Any

try:
    import PIL

    PIL_AVAILABLE = True
except ModuleNotFoundError:
    PIL_AVAILABLE = False
    PIL = None


class OpenCVHandler:
    """
    Keeps track of the current Open CV support state
    """

    available = True
    "Defines if OpenCV is available"


_cv = None
"Holds the OpenCV module if it's available"
_cv_available = None
"Defines if OpenCV is available"
_cv_access_lock = RLock()
"Thread-secure access for first initialization"


def get_opencv() -> ModuleType | None:
    """
    Returns the OpenCV module handle if available

    :return: The module handle, None otherwise
    """
    global _cv_available, _cv
    if not OpenCVHandler.available:
        return None
    with _cv_access_lock:
        if _cv_available is None:
            try:
                _cv = importlib.import_module("cv2")
                _cv_available = True
            except ModuleNotFoundError:
                _cv_available = False
        return _cv


class ImsFramework(enum.Enum):
    """
    Definition of available frameworks for storing and modifying pixel data
    in ImageStag
    """

    PIL = "PIL"
    "Prefer using a Pillow image handle to store the pixel data"
    RAW = "RAW"
    """
    Prefer using numpy to store the image data. RGB and RGBA images are 
    represented in RGB/RGBA order
    """
    CV = "CV"
    """
    Prefer using OpenCV to store the pixel data. RGB and RGBA images are 
    represented in BGR/BGRA order
    """

    @classmethod
    def _missing_(cls, value: object) -> Any:
        missing_dict = {"PIL": cls.PIL, "RAW": cls.RAW, "CV": cls.CV}
        if value in missing_dict:
            return missing_dict[value]
        return None


__all__ = ["ImsFramework", "get_opencv", "PIL_AVAILABLE", "PIL"]
