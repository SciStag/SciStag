"""
Implements the checkerboard shape :class:`Checkerboard`
"""
from __future__ import annotations
import math
import typing

from scistag.imagestag import (
    Canvas,
    Color,
    Colors,
    Bounding2D,
    Pos2D,
    Size2D,
    ColorTypes,
)
from scistag.imagestag.bounding import Bounding2DTypes
from scistag.imagestag.pos2d import Pos2DTypes
from scistag.imagestag.size2d import Size2DTypes
from scistag.shapestag import Shape


class Checkerboard(Shape):
    """
    A checkerboard either defined by a count of columns and rows or an area
    it shall cover.

    Draws a grid of rectangles using two different colors, for example to
    draw a checkerboard for calibration purposes or to use it as background,
    e.g. for transparent images to be better able to distinguish transparent
    and non-transparent areas as seen in common photo editing apps.
    """

    tile_size: Size2D = Size2D(16, 16)
    "The tile size in pixels"
    color_a: Color = Colors.BLACK
    "The first color (used for all uneven fields)"
    color_b: Color = Colors.WHITE
    "The first color (used for all even fields)"
    columns: int = 16
    "The column count (horizontal grid width)"
    rows: int = 16
    "The row count (vertical grid height)"

    HASHABLE_PROPERTIES: typing.ClassVar = Shape.HASHABLE_PROPERTIES | {
        "color_a",
        "color_b",
        "tile_size",
        "bounding",
        "offset",
    }

    def __init__(
        self,
        bounding: Bounding2DTypes = None,
        col_row_count: Size2DTypes | None = None,
        tile_size: float = 16.0,
        color_a: ColorTypes = Colors.BLACK,
        color_b: ColorTypes = Colors.WHITE,
        offset: Pos2DTypes | None = None,
    ):
        """
        :param bounding: The region to be covered in pixels
        :param col_row_count: The count of columns and rows (alternative to region)
        :param tile_size: The size per tile
        :param color_a: The first color (used for all uneven fields (col+row))
        :param color_b: The second color (used for all even fields (col+row))
        :param offset: The offset in pixels by which the grid shall be moved
        """
        super().__init__(
            self.__class__.__name__, hashable_properties=self.HASHABLE_PROPERTIES
        )
        if bounding is None and col_row_count is None:
            raise ValueError("Neither region nor size passed")
        if bounding is not None and col_row_count is not None:
            raise ValueError("You have to either pass region OR size")
        if tile_size is None or tile_size <= 0:
            raise ValueError("Invalid tile size, has to be >0")
        self.tile_size = Size2D(tile_size, tile_size)
        "The tile size in pixels"
        self.bounding = Bounding2D(bounding) if bounding is not None else None
        "The region to be covered overall"
        if col_row_count is not None:
            int_size = Size2D(col_row_count).to_int_tuple()
            self.bounding = Bounding2D(
                pos=(0, 0) if offset is None else Pos2D(offset),
                size=(
                    int_size[0] * self.tile_size.width,
                    int_size[1] * self.tile_size.height,
                ),
            )
        self.color_a = color_a if isinstance(color_a, Color) else Color(color_a)
        "The first color (used for all uneven fields)"
        self.color_b = color_b if isinstance(color_b, Color) else Color(color_b)
        "The first color (used for all even fields)"
        col_row_count = self.bounding.get_size_tuple()
        self.columns = int(math.ceil(col_row_count[0] / self.tile_size.width))
        "The column count (horizontal grid width)"
        self.rows = int(math.ceil(col_row_count[1] / self.tile_size.height))
        "The row count (vertical grid height)"

    def draw(self, target: Canvas, options: dict | None = None):
        ox, oy = self.bounding.pos.to_tuple()
        sx, sy = self.tile_size.width, self.tile_size.height
        # collect geometry for all rectangles
        dark_rects = []
        bright_rects = []
        for cur_row in range(self.rows):
            cur_y = oy + cur_row * sy
            for cur_col in range(self.columns):
                cur_x = ox + cur_col * sy
                if (cur_col + cur_row) % 2 == 0:
                    bright_rects.append(
                        ((cur_x, cur_y), (cur_x + sx - 1, cur_y + sy - 1))
                    )
                else:
                    dark_rects.append(
                        ((cur_x, cur_y), (cur_x + sx - 1, cur_y + sy - 1))
                    )
        # draw dark and bright rects in one batch each
        target.rectangle_list(bright_rects, single_color=self.color_b.to_int_rgba())
        target.rectangle_list(dark_rects, single_color=self.color_a.to_int_rgba())
