"""
Implements the class :class:`PyPlotLogContext` which allows the easy,
thread-safe integration of matplotlib plots into a VisualLog.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import LogBuilder


class PyPlotLogContext:
    """
    Defines an enclosed, multi-thread safe PyPlot logging context.

    When the context is left it adds the latest figure to the VisualLog
    it is associated to.

    Is created via LogBuilder.pyplot, see :meth:`LogBuilder.pyplot`
    """

    def __init__(
        self,
        target_log: "LogBuilder",
        assertion_name: str | None = None,
        assertion_hash: str | None = None,
        br: bool = False,
    ):
        """
        :param target_log: Defines the target into which we shall log
        :param assertion_name: If the figure shall be asserted, it's unique
            identifier.
        :param assertion_hash: If the figure shall be asserted via hash the
            hash value of its image's pixels.
        :param br: Defines if the figure shall be followed by a linebreak.

            This value has no impact in assertion mode.
        """
        from scistag.plotstag import MPLock

        self.target_log = target_log
        "The log into which we shall write when the figure is finished"
        self.mp_lock = MPLock()
        """
        The pyplot thread access lock so only one thread can use pyplot as at 
        time
        """
        self.plt_handle = None
        "The plot handle to the matplotlib.pyplot library"
        self.assertion_name = assertion_name
        "If the figure shall be asserted, it's unique identifier"
        self.assertion_hash = assertion_hash
        """
        If the figure shall be asserted via hash the hash value of its image's 
        pixels.
        """
        self.br = br
        """Defines if a linebreak shall be printed after the figure"""

    def __enter__(self):
        self.plt_handle = self.mp_lock.__enter__()
        return self.plt_handle

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.assertion_name is None:  # basic logging?
            self.target_log.figure(self.plt_handle.gcf(), br=self.br)
        else:  # logging with assert
            self.target_log.test.assert_figure(
                self.assertion_name, self.plt_handle.gcf(), hash_val=self.assertion_hash
            )
        self.mp_lock.__exit__(exc_type, exc_val, exc_tb)
