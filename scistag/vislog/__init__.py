"""
Integrates VisualLog and VisualTestLog
"""

from .visual_log import VisualLog

from .visual_test_log import VisualTestLog
from .visual_log_builder import VisualLogBuilder, VisualLogBackup
from .extensions.builder_extension import BuilderExtension
from .common.log_statistics import LogStatistics
from .extensions.cell_sugar import cell
from .extensions.cell_logger import Cell

__all__ = [
    "VisualLog",
    "VisualTestLog",
    "VisualLogBuilder",
    "VisualLogBackup",
    "LogStatistics",
    "BuilderExtension",
    "cell",
    "Cell",
]
