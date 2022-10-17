"""
Integrates VisualLog and VisualTestLog
"""

from .visual_log import VisualLog
from .visual_test_log import VisualTestLog
from ..visual_livelog import VisualLiveLog

__all__ = ["VisualLog", "VisualTestLog", "VisualLiveLog"]
