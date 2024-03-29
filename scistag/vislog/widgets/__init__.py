"""
Defines the module for Widget extensions for VisualLog
"""
from .comparison import LComparison
from .event import LEvent
from .base_events import LValueChangedEvent
from .log_widget import LWidget
from .select import LSelect
from .timer import LTimer, LTimerTickEvent
from .button import LButton, LClickEvent
from .slider import LSlider
from .file_upload import LFileUpload, LFileUploadEvent

__all__ = [
    "LWidget",
    "LValueWidget",
    "LButton",
    "LClickEvent",
    "LSlider",
    "LTimer",
    "LTimerTickEvent",
    "LEvent",
    "LValueChangedEvent",
    "LFileUpload",
    "LFileUploadEvent",
    "LComparison",
    "LSelect",
]

from .value_widget import LValueWidget
