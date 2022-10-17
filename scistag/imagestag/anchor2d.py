"""
Defines the :class:`Anchor2D` class which defines how an object is drawn
relative to the position passed.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Literal, Union

from .size2d import Size2D, Size2DTypes
from .pos2d import Pos2D


class Anchor2D(IntEnum):
    """
    Defines how an origin (such as a position) is interpreted when a shape such
    as a rectangle, a circle or a multi-line text is painted just given a
    position and a size is painted.
    """
    TOP_LEFT = 0
    """
    The origin is the shape's top left edge - everything is painted to the right
    and bottom of it.
    """
    TOP = 1
    """
    The origin is the shape's top center edge - everything is painted equally
    to the left and right of it and to the bottom.
    """
    TOP_RIGHT = 2
    """
    The origin is the shape's top right edge - everything is painted to the
    left and the bottom of it.
    """
    CENTER_LEFT = 3
    """
    The origin is the shape's center left edge - everything is painted equally
    to the top and bottom of it and to the right.
    """
    CENTER = 4
    """
    The origin is the shape's center - everything is painted equally to the
    left, right, top and bottom of it.
    """
    CENTER_RIGHT = 5
    """
    The origin is the shape's center right - everything is painted equally to
    the top and bottom of it to the right.
    """
    BOTTOM_LEFT = 6
    """
    The origin is the shape's bottom left - everything is painted to the right
    and to the top of it.
    """
    BOTTOM = 7
    """
    The origin is the shape's bottom center - everything is painted equally
    to the left and right of it to the top.
    """
    BOTTOM_RIGHT = 8
    """
    The origin is the shape's bottom right - everything is painted to the left
    and top of it.
    """

    @classmethod
    def _missing_(cls, value: Anchor2D | str):
        """
        Initializes an anchor using a string

        :param value: The integer enum value or an alternative
            string shortcode representation. Valid values are:
            - "tl" / "topLeft" - TOP_LEFT
            - "t" /"top" - TOP (center)
            - "tr" / "topRight" - TOP_RIGHT
            - "cl" / "centerLeft" - CENTER_LEFT
            - "c" / "center" - CENTER (horizontally and vertically)
            - "cr" / "centerRight" - CENTER_RIGHT
            - "bl" / "bottomLeft" - BOTTOM_LEFT
            - "b" / "bottom" - BOTTOM (center)
            - "br" / "bottomRight" - BOTTOM_RIGHT
        :return: The  Anchor2D enum value
        """

        class Definitions:
            values = {
                "tl": cls.TOP_LEFT,
                "topLeft": cls.TOP_LEFT,
                "t": cls.TOP,
                "top": cls.TOP,
                "tr": cls.TOP_RIGHT,
                "topRight": cls.TOP_RIGHT,
                "cl": cls.CENTER_LEFT,
                "centerLeft": cls.CENTER_LEFT,
                "c": cls.CENTER,
                "center": cls.CENTER,
                "cr": cls.CENTER_RIGHT,
                "centerRight": cls.CENTER_RIGHT,
                "bl": cls.BOTTOM_LEFT,
                "bottomLeft": cls.BOTTOM_LEFT,
                "b": cls.BOTTOM,
                "bottom": cls.BOTTOM,
                "br": cls.BOTTOM_RIGHT,
                "bottomRight": cls.BOTTOM_RIGHT
            }

        if value not in Definitions.values:
            raise ValueError("Unknown anchor literal. See Anchor2D()")
        return Definitions.values[value]

    def get_position_shift(self, size: Size2DTypes) -> tuple[float, float]:
        """
        Gets the anchor caused position shifting at given object size

        E.g. a LEFT_TOP anchor will never modify the position at all, a
        CENTER anchor will be the position by half of size.width to the left
        and half of size.height to the right etc. so the painted object
        will be centered around the (original) pos effectively when being
        painted at the now (modified) pos.

        :param size: The object's size (circle, rectangle, image etc.)
        :return: The amount of pixels by which the output shall be shifted,
            to be added to the original position
        """
        if self == Anchor2D.TOP_LEFT:
            return 0.0, 0.0
        if not isinstance(size, Size2D):
            size = Size2D(size)
        x_align = self % 3
        y_align = self // 3
        return (0.0 if x_align == 0 else  # left
                -size.width / 2 if x_align == 1 else  # h center
                -size.width,  # right
                0.0 if y_align == 0 else  # top
                -size.height / 2 if y_align == 1 else  # v center
                -size.height)  # bottom

    def shift_position(self, pos: Pos2D, size: Size2D,
                       round_shift: bool = False) -> Pos2D:
        """
        Adjusts the position by the amount of pixels this anchor will shift
        the painting origin of the position caused through this anchor.

        E.g. a LEFT_TOP anchor will never modify the position at all, a
        CENTER anchor will be the position by half of size.width to the left
        and half of size.height to the right etc. so the painted object
        will be centered around the (original) pos effectively when being
        painted at the now (modified) pos.

        :param pos: The position to modify. (this object will be modified)
        :param size: The size of the object to be drawn
        :param round_shift: If defined the shifting will be rounded
        :return: The modified position
        """
        shift = self.get_position_shift(size)
        if round_shift:
            pos.x = round(pos.x + shift[0])
            pos.y = round(pos.y + shift[1])
        else:
            pos.x += shift[0]
            pos.y += shift[1]
        return pos


Anchor2DLiterals = Literal["tl", "topLeft", "t", "top", "tr", "topRight",
                           "cl", "centerLeft", "c", "center", "cr",
                           "centerRight", "bl", "bottomLeft",
                           "b", "bottom", "br", "bottomRight"]
"""
Shortcode alternative which can be passed to most functions supporting anchors 
to minimize the amount of imports required.
"""

Anchor2DTypes = Union[Anchor2D, Anchor2DLiterals]
"Ways to define an anchor type, either as Anchor2D enum or string literal"

__all__ = [Anchor2D, Anchor2DLiterals]
