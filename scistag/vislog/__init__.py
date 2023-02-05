"""
Integrates VisualLog and VisualTestLog
"""
from .common.cache_log_ref import CLRef
from .sessions.page_session import MD, HTML, TXT, CONSOLE
from .visual_log import VisualLog

from .visual_test_log import VisualTestLog
from .log_builder import LogBuilder
from .common.log_backup import LogBackup
from .extensions.builder_extension import BuilderExtension
from .common.log_statistics import LogStatistics
from .extensions.cell_logger import Cell
from .log_elements import HTMLCode, MDCode
from .cells import cell, section, data, stream, once

__all__ = [
    "VisualLog",
    "VisualTestLog",
    "LogBuilder",
    "CLRef",
    "LogStatistics",
    "BuilderExtension",
    "Cell",
    "HTMLCode",
    "MDCode",
    "MD",
    "HTML",
    "TXT",
    "CONSOLE",
    "cell",
    "section",
    "data",
    "stream",
    "once",
]
