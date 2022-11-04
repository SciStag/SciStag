"""
Implements the class :class:`PyPlotLogContext` which allows the easy,
thread-safe integration of matplotlib plots into a VisualLog.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.logstag.visual_log.visual_log_builder import VisualLogBuilder


class PyPlotLogContext:
    """
    Defines an enclosed, multi-thread safe PyPlot logging context.

    When the context is left it adds the latest figure to the VisualLog
    it is associated to.

    Is created via VisualLogBuilder.pyplot, see :meth:`VisualLogBuilder.pyplot`
    """

    def __init__(self, target_log: "VisualLogBuilder"):
        from scistag.plotstag import MPLock
        self.target_log = target_log
        self.mp_lock = MPLock()
        self.plt_handle = None

    def __enter__(self):
        self.plt_handle = self.mp_lock.__enter__()
        return self.plt_handle

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.target_log.figure(self.plt_handle.gcf())
        self.mp_lock.__exit__(exc_type, exc_val, exc_tb)
