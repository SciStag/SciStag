"""
Integrates VisualLog and VisualTestLog
"""

from .visual_log import VisualLog

from .visual_test_log import VisualTestLog
from .visual_log_builder import VisualLogBuilder
from .visual_log_builder_extension import VisualLogBuilderExtension
from .visual_log_statistics import VisualLogStatistics

__all__ = ["VisualLog", "VisualTestLog", "VisualLogBuilder",
           "VisualLogStatistics", "VisualLogBuilderExtension"]
