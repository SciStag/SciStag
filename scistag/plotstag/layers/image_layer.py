"""
Implements the :class:`ImageLayer: which visualizes an image on a :class:`Plot`.
"""

from __future__ import annotations

from typing import Literal

import numpy as np

from scistag.common import get_global_cache
from scistag.imagestag import Canvas, Image, Size2D, Colors, PixelFormat, Color
from scistag.plotstag.plot_layer import PlotLayer, ValueRange1D
from scistag.shapestag.checkerboard import Checkerboard

CHECKERBOARD_BACKGROUND = "cb"


class ImageLayer(PlotLayer):
    """
    Visualizes an image on a plot.
    """

    def __init__(self, image: Image | np.ndarray,
                 size_ratio: float | tuple[float, float] | None = None,
                 bg_fill: str | Color | None = "cb"):
        """
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
        if Image is None:
            raise ValueError("Invalid image")
        if size_ratio is not None:
            if isinstance(size_ratio, float):
                size_ratio = \
                    (size_ratio, size_ratio)
            if size_ratio[0] <= 0 or size_ratio[1] <= 0:
                raise ValueError("Invalid size factor")
        super().__init__()
        if not isinstance(image, Image):
            image = Image(image)
        self.value_range = (ValueRange1D(0.0, image.width),
                            ValueRange1D(0.0, image.height))
        self.original_size_factor = size_ratio
        if self.original_size_factor is not None:
            osf = self.original_size_factor
            self.fixed_size = Size2D(image.width * osf[0],
                                     image.height * osf[1])
        self._image = image
        "The image to be plotted"
        self._scaled_image = image
        "The scaled version of the image to be plotted"
        self.needs_clipping = image.is_transparent()
        """
        Defines if the whole content shall be rendered into a separated
        clippable canvas
        """
        self.bg_fill: str | Color | None = bg_fill
        """
        Defines the way the background is filled if he image is alpha-
        transparent. Either with a color or a checkerboard ("cb")
        """

    def update_layout(self, desired_size: Size2D | None = None,
                      forced_size: Size2D | None = None):
        super().update_layout(desired_size=None, forced_size=forced_size)
        if forced_size is not None:
            desired_size = forced_size
            self.size = None
        if self.size is None:  # keep aspect ratio in proposed area
            scaling_x = desired_size.width / self._image.width
            scaling_y = desired_size.height / self._image.height
            eff_scaling = min(scaling_x, scaling_y)
            self.size = Size2D(round(self._image.width * eff_scaling),
                               round(self._image.height * eff_scaling))

    @staticmethod
    def generate_checkerboard(tile_size: int,
                              color_a=Colors.LIGHT_GRAY,
                              color_b=Colors.WHITE) -> Image:
        """
        Renders a checkerboard as background for transparent images

        :param tile_size: The size of a tile in pixels
        :param color_a: The primary tile color
        :param color_b: The secondary tile color
        :return: The checkerboard graphic
        """
        repetition = max(256 // tile_size, 2)
        cb = Checkerboard(col_row_count=(repetition, repetition),
                          tile_size=tile_size,
                          color_a=color_a,
                          color_b=color_b)
        return cb.to_image()

    def paint(self, canvas: Canvas):
        super().paint(canvas)
        size_pixels = self.size.to_int_tuple()
        if size_pixels[0] <= 0 or size_pixels[1] <= 0:
            return
        if self._scaled_image is None or \
                self._scaled_image.get_size() != size_pixels:
            self._scaled_image = self._image.resized(size_pixels)
        if self._scaled_image.pixel_format == PixelFormat.RGBA and \
                self.bg_fill is not None:
            if self.bg_fill == CHECKERBOARD_BACKGROUND:
                cb = self.get_cb_pattern()
                canvas.pattern(cb, ((0, 0),
                                    (self._scaled_image.width,
                                     self._scaled_image.height)))
            elif isinstance(self.bg_fill, Color):
                canvas.rect(pos=(0, 0),
                            size=(self._scaled_image.width,
                                  self._scaled_image.height),
                            color=self.bg_fill)
        canvas.draw_image(self._scaled_image, (0, 0))

    @classmethod
    def get_cb_pattern(cls, tile_size: int = 16,
                       style: Literal[
                           "graywhite", "neon"] = "graywhite") -> Image:
        """
        Returns an image with a checkerboard pattern

        :param tile_size: The tile size in pixels
        :param style: Defines the checkerboard's color style, either graywhite
            or neon as of now.
        :return: An image full of checkerboard patterns which can e.g be sued
            as background for transparent images.
        """
        cache = get_global_cache()
        if style == "neon":
            col_a = Colors.CYAN
            col_b = Colors.MAGENTA
        else:
            col_a = Colors.WHITE
            col_b = Colors.LIGHT_GRAY
        cb: Image = cache.cache(
            f"plotstag.ImageLayer.backgroundGrid{tile_size}{style}",
            cls.generate_checkerboard, tile_size, col_b, col_a)
        return cb
