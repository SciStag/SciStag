# TODO Work in progress

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.logstag.visual_log import VisualLog


class PyPlotLogContext:
    def __init__(self, target_log: "VisualLog"):
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
