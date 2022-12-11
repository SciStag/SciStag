"""
Implements the :class:`Plot` class which visualizes a single plot within a
:class:`Figure`.
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Union

import numpy as np

from scistag.imagestag.bounding import Bounding2D
from scistag.imagestag.size2d import Size2DTypes
from scistag.imagestag.font import Font, VTextAlignment
from scistag.imagestag.font_registry import FontRegistry
from scistag.imagestag import Size2D, Pos2D, Canvas, Colors, Image, Color
from scistag.plotstag.plot_layer import PlotLayer

if TYPE_CHECKING:
    from scistag.plotstag.figure import Figure
    import matplotlib.pyplot as plt


class Plot:
    """
    Defines a single plot.

    A plot defines an area within a :class:`Figure` which can consist of
    one or multiple plots overlaying of each other using the
    :class:`PlotLayer`s provided such as line charts, scatter plots, images
    etc.
    """

    def __init__(self, target_size: Size2DTypes | None = None):
        """
        :param target_size: The target size in pixels
        """
        self.target_size = Size2D(target_size) if target_size is not None else None
        "Desired target size in pixels"
        self.size: Size2D = target_size
        "Plot's effective size in pixels (as far as defined)"
        self.layers: list[PlotLayer] = []
        "Single data visualization layers (the real plots)"
        self.border_width = 2.0
        "Border width in pixels"
        self.border_margins = [self.border_width] * 4
        "Border margin in pixels"
        self.border_color = Colors.BLACK
        "Border color"
        self.margins = [margin for margin in self.border_margins]
        """
        Margin around the main layers in pixels on each side
        (left, top, right, bottom)
        """
        self.layer_pos = Pos2D(self.margins[0], self.margins[1])
        "Position at which the layers shall be plotted"
        self.layer_size = Size2D(0, 0)
        "The layer size in pixels"
        self._figure: Optional["Figure"] = None
        "Figure which contains this plot"
        self.column = 0
        "Column in which the plot is displayed. Auto-assigned by the figure"
        self.row = 0
        "Row in which the plot is displayed. Auto-assigned by the figure"
        self.index = 0
        "Enumeration index of the plot. Auto-assigned by the figure"
        self.title = None
        "The plot's title"
        self.title_height = 0.0
        "The title's size in pixels"
        self._title_font: Font | None = None
        "Cached title font"
        self.title_spacing: tuple[float, float] = (0.0, 0.0)
        "Space above and below the title"
        self.title_color = Colors.BLACK
        "The title's color"

    def _repr_png_(self) -> bytes:
        """
        Creates a PNG representation for Jupyter

        :return: The PNG data
        """
        return self.render().to_png()

    def set_figure(self, figure: "Figure") -> None:
        """
        Links the plot to the figure which contains it

        :param figure: The figure
        """
        self._figure = figure
        # use defaults if set
        if figure.default_plot_border_margin_size is not None:
            self.border_margins = [figure.default_plot_border_margin_size] * 4
        if figure.default_plot_border_width is not None:
            self.border_width = figure.default_plot_border_width

    def get_figure(self):
        """
        Returns the plot's figure.

        If no figure was assigned yet it will automatically create it

        :return: The figure
        """
        if self._figure is None:
            from scistag.plotstag.figure import Figure

            self._figure = Figure()
            self._figure.set_plot(self)
        return self._figure

    def add_layer(self, layer: PlotLayer):
        """
        Adds a layer to this plot

        :param layer: The new layer
        """
        self.layers.append(layer)

    def update_margins(self):
        """
        Updates the current layer offset
        :return:
        """
        self.margins = [margin for margin in self.border_margins]
        self.margins[1] += self.title_height
        self.layer_pos = Pos2D(self.margins[0], self.margins[1])

    def set_title(self, title: str | None) -> Plot:
        """
        Sets the plot's title

        :param title: The plot's title text. None do deactivate the title
        :return: The plot
        """
        figure = self.get_figure()
        self.title = title
        if self.title is None:
            self.title_height = 0.0
            return self
        self.title_spacing = figure.default_plot_title_spacing
        self._title_font = FontRegistry.get_font(
            figure.default_font, size=figure.default_plot_title_size
        )
        "The title's size in pixels"
        text_size = self._title_font.get_text_size(title)
        self.title_height = (
            text_size.height + self.title_spacing[0] + self.title_spacing[1]
        )
        self.update_margins()
        return self

    def update_layout(self):
        """
        Updates the plot's layout to compute the plot's efficient size
        """

        margins = self.margins
        hor_margins = margins[0] + margins[2]
        ver_margins = margins[1] + margins[3]
        plot_default_size: Size2D = self.get_figure().plot_default_size
        if self.target_size is not None:
            self.size = self.target_size
            forced_size = Size2D(
                self.size.width - hor_margins, self.size.width - ver_margins
            )
            for layer in self.layers:
                layer.update_layout(forced_size=forced_size)
        elif len(self.layers) == 0:
            self.size = Size2D(0, 0)
            self.layer_size = self.size
        else:
            self.size = plot_default_size
            desired_size = Size2D(
                plot_default_size.width - hor_margins,
                plot_default_size.width - ver_margins,
            )
            for layer in self.layers:
                if layer.fixed_size is not None:
                    desired_size = layer.fixed_size
            for layer in self.layers:
                layer.update_layout(desired_size=desired_size)
        if len(self.layers):
            layer_zero = self.layers[0]
            self.size = Size2D(
                layer_zero.size.width + hor_margins,
                layer_zero.size.height + ver_margins,
            )
            self.layer_size = layer_zero.size
        else:
            self.layer_size = Size2D(0, 0)

    def paint(self, canvas: Canvas):
        """
        Paints the plot and all of it's layers and subcomponents such as
        the legend.

        :param canvas: The target canvas
        """
        self._paint_decoration(canvas)
        if not self.size.is_empty():
            clipping = any([layer.needs_clipping for layer in self.layers])
            layer_offset = self.layer_pos.to_int_tuple()
            org_canvas = canvas
            if clipping:
                first_layer = self.layers[0]
                canvas_size = first_layer.size.to_int_tuple()
                image = canvas.to_image()
                off = canvas.transform(layer_offset)
                image = image.cropped(
                    box=(
                        off[0],
                        off[1],
                        off[0] + canvas_size[0],
                        off[1] + canvas_size[1],
                    )
                )
                canvas = image.to_canvas()
            for layer in self.layers:
                if not clipping:
                    canvas.push_state()
                    canvas.add_offset_shift(layer_offset)
                layer.paint(canvas)
                if not clipping:
                    canvas.pop_state()
            if clipping:
                org_canvas.draw_image(canvas.to_image(), layer_offset)

    def _paint_decoration(self, canvas):
        """
        Paints the decoration such as border and title

        :param canvas: The target canvas
        """
        margins = self.margins
        if self.border_width != 0.0 and not self.size.is_empty():
            ul = (
                margins[0] - self.border_margins[0],
                margins[1] - self.border_margins[1],
            )
            lr = (
                self.size.width - margins[2] + self.border_margins[2],
                self.size.height - margins[3] + self.border_margins[3],
            )
            canvas.rect(
                bounding=Bounding2D(pos=ul, lr=lr),
                color=None,
                outline_width=int(round(self.border_width)),
                outline_color=self.border_color,
            )

        if self.title is not None:
            text_size = self._title_font.get_text_size(self.title)
            center_x = (
                self.layer_pos.x + self.layer_size.width / 2 - text_size.width / 2
            )
            y_off = self.title_spacing[0] + self._title_font.ascend // 2
            canvas.text(
                Pos2D(center_x, y_off),
                font=self._title_font,
                v_align=VTextAlignment.CENTER,
                text=self.title,
                color=self.title_color,
            )

    def render(self) -> Image:
        """
        Renders the plot's figure

        :return: The visualization of the plot as :class:`Image`
        """
        self.get_figure()
        return self._figure.render()

    def add_image(
        self,
        image: Image | np.ndarray,
        size_ratio: float | tuple[float, float] | None = None,
        bg_fill: str | Color | None = "cb",
    ) -> Plot:
        """
        Adds an image layer

        :param image: The image to plot
        :param size_ratio: The size ratio from the image's or
            matrix original size to effective pixels. This can be used to
            plot images in original size rather than being auto-scaled through
            the plot's configuration.

            - 1.0 = keep the original size.
            - 0.5 = 50% of the original size
            - ...
        :param bg_fill: Defines the background which shall be used if
            the image is alpha-transparent. If a color is passed the
            whole background will be filled with given color.

            "cb" (checkerboard) by default.
        """
        from scistag.plotstag.layers.image_layer import ImageLayer

        self.add_layer(ImageLayer(image=image, size_ratio=size_ratio, bg_fill=bg_fill))
        return self

    def add_matplot(
        self,
        figure: Union["plt.Figure", None] = None,
        size_ratio: float | None = None,
        **params,
    ):
        """
        Adds a matplotlib figure as image layer to the plot

        :param figure: The figure to be added
        :param size_ratio: If set the plot will be scaled with given factor
        :param params: The parameters to be passed to the figure if a new figure
            shall be created.
        :return: The Plot if a figure was passed (and so no further action is
            required).

            Otherwise an MPLayerLock which shall be used the following way:

            ..  code-block:: python

                with my_plot.add_matplot() as plt:
                    plt.title(...)
                    plt.imshow(...)
        """
        from scistag.plotstag.matplot_helper import MPHelper
        from scistag.plotstag.layers.matplot_layer import MPLayerLock

        if figure is not None:
            self.add_image(
                MPHelper.figure_to_image(figure), size_ratio=size_ratio, bg_fill=None
            )
        else:
            return MPLayerLock(self, size_ratio=size_ratio, **params)
