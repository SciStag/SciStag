"""
Helper class for adding a matplotlib log as layer into a PlotStag plot
"""
from __future__ import annotations

from scistag.plotstag.plot import Plot
from scistag.plotstag.matplot_lock import MPLock

from scistag.plotstag.matplot_helper import MPHelper


class MPLayerLock(MPLock):
    """
    Helper class which helps inserting an image layer to a PlotStag by
    automatically fetching the latest current matplotlib figure upon
    exiting
    """

    def __init__(self, target_plot: Plot, size_ratio: float | None = None, **params):
        """
        :param target_plot: The plot to which the figure shall be added
        :param size_ratio: If set the matplot plot's original size will
            be enforced.
        :param params: The parameters to be passed into the figure
        """
        super().__init__()
        self.target_plot = target_plot
        "The plot to which the matplot figure shall be added"
        self.params = params
        self.size_ratio = size_ratio
        self.figure = None

    def __enter__(self):
        res = super().__enter__()
        import matplotlib.pyplot as plt

        self.figure = plt.figure(**self.params)
        return res

    def __exit__(self, exc_type, exc_val, exc_tb):
        image = MPHelper.figure_to_image(self.figure)
        self.target_plot.add_image(image, bg_fill=None, size_ratio=self.size_ratio)
        if self.figure:
            del self.figure
        super(MPLayerLock, self).__exit__(exc_type, exc_val, exc_tb)
