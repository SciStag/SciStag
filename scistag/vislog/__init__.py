"""
Integrates VisualLog and VisualTestLog
"""
from .sessions.page_session import MD, HTML, TXT
from .visual_log import VisualLog

from .visual_test_log import VisualTestLog
from .visual_log_builder import LogBuilder, LogBackup, MIMETYPE_HTML, MIMETYPE_MARKDOWN
from .extensions.builder_extension import BuilderExtension
from .common.log_statistics import LogStatistics
from .extensions.cell_sugar import cell
from .extensions.cell_logger import Cell
from .log_elements import HTMLCode, MDCode

__all__ = [
    "VisualLog",
    "VisualTestLog",
    "LogBuilder",
    "LogBackup",
    "LogStatistics",
    "BuilderExtension",
    "cell",
    "Cell",
    "HTMLCode",
    "MDCode",
    "MIMETYPE_MARKDOWN",
    "MIMETYPE_HTML",
    "MD",
    "HTML",
    "TXT",
]
