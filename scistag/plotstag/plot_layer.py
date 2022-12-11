"""
The :class:`PlotLayer` visualizes a plot's content such as a bar graph,
a scatter plot etc. It visualizes the area between the axes, defines
the value range on all axes' and the transformation.
"""
from __future__ import annotations

from dataclasses import dataclass

from abc import abstractmethod

from scistag.imagestag import Size2D, Canvas


@dataclass
class ValueRange1D:
    """
    Defines the value range on axis
    """

    min_Val: float = 0.0
    max_val: float = 0.0


PlotValueRange2D = tuple[ValueRange1D, ValueRange1D]
"Defines the value range of a 2D plot (X,Y)"

PlotValueRange3D = tuple[ValueRange1D, ValueRange1D, ValueRange1D]
"Defines the value range of a 3D plot (X,Y,Z)"


class PlotLayer:
    """
    The :class:`PlotLayer` visualizes a plot's content.

    Such content types can be bar graphs, scatter plots, line graphs, pie
    charts, images, matrices etc.
    """

    def __init__(self, fixed_size: Size2D | None = None):
        """
        :param fixed_size: If specified this layer will try to enforce the
            size specified in pixels, e.g to guarantee a 1:1 projection of an
            image or matrix with a desired content cell to pixel ratio.
        """
        self.fixed_size: Size2D | None = fixed_size
        "The fixed size. If specified the plot will try to enforce this size"
        self.size: Size2D = Size2D(100, 100)
        "The effective size of this layer in pixels"
        self.value_range: PlotValueRange2D | PlotValueRange3D = (
            ValueRange1D(0.0, 0.0),
            ValueRange1D(0.0, 0.0),
        )
        "The range of the values stored in this layer"
        self.needs_clipping = False
        """
        Defines if the layer needs to be precisely clipped because it can
        not be guaranteed that all elements will be painted precisely inside.
        """

    def update_layout(
        self, desired_size: Size2D | None = None, forced_size: Size2D | None = None
    ):
        """
        Updates the layout (especially .size) with the size foreseen by the plot
        :param desired_size: The proposed size by the plot
        :param forced_size: Enforced size i f the size can under no
            circumstances be influenced by a layer.
        """
        if forced_size:
            self.size = forced_size
        elif self.fixed_size is None:
            self.size = desired_size
        else:
            self.size = self.fixed_size

    @abstractmethod
    def paint(self, canvas: Canvas):
        """
        Paints the layer's content
        :param canvas: The target canvas into which the content shall be
            painted.
        """
        pass
