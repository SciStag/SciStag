"""
Implements the location, size and bounding definition classes Size2D, Pos2D and
Bounding2D.

These are for example required for painting operations in ImageStag and defining
a Widget's layout and position in SlideStag.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Union

from .size2d import Size2D, Size2DTypes
from .pos2d import Pos2D, Pos2DTypes

Bounding2DTypes = Union[
    "Bounding2D",
    tuple[int, int, int, int],
    tuple[float, float, float, float],
    tuple[Pos2DTypes, Pos2DTypes],
    tuple[Pos2DTypes, Size2DTypes],
]
"""
The supported bounding types. Either a Bounding2D, a 4-tuple of either integers 
or floats defining x,y,x2,y2 or a 2-tuple of the supported position and size 
types.

In case of 2-tuples as the type definition is ambiguous here due to Pos2DTypes
and Size2DTypes: If values are passed in the form ((a,b),(c,d)) c and
will be interpreted as width and height. Only if the second tuple element 
is a real object of type :class:`Pos2D` it will be interpreted as such.
"""


@dataclass
class Bounding2D:
    """
    Defines the 2D-bounding of a visual element by it's upper left and lower
    right corner.
    """

    pos: Pos2D
    """
    The position of the upper left coordinate. x and y should always be equal or 
    smaller than x and y of lr
    """
    lr: Pos2D
    """
    The position of the lower right coordinate. x and y should always be equal 
    or greater than x and y of pos.
    """

    def __init__(
        self,
        value: Bounding2DTypes | None = None,
        pos: Pos2DTypes | None = None,
        lr: Pos2DTypes | None = None,
        size: Size2DTypes | None = None,
    ):
        """
        :param value: The bounding value (or a bounding to copy) as defined by
            :class:`Bounding2DTypes`.
        :param pos: The explicit upper left coordinate
        :param lr: The explicit lower right coordinate
        :param size: The size, relative to the upper left coordinate or lower
            right coordinate.
        """
        if value is not None and isinstance(value, Bounding2D):
            self.pos = Pos2D(value.pos)
            self.lr = Pos2D(value.lr)
            return
        if pos is not None:  # ul + lr or size
            self.pos = Pos2D(pos)
            if size is not None:
                size = size if isinstance(size, Size2D) else Size2D(size)
                self.lr = Pos2D(x=self.pos.x + size.width, y=self.pos.y + size.height)
                return
            if lr is not None:
                self.lr = Pos2D(lr)
                return
            raise ValueError(
                "Neither lr nor size defined but required in" " combination with ul"
            )
        if lr is not None:  # lr + size
            if size is None:
                raise ValueError(
                    "Neither ul nor size defined but required in " "combination with lr"
                )
            self.pos = Pos2D(x=lr.x - size.width, y=lr.y - size.height)
            self.lr = Pos2D(lr)
            return
        if not isinstance(value, tuple):
            raise TypeError("Unsupported data type")
        if len(value) == 2:  # Pos, Pos or Pos, Size tuple
            self.pos = Pos2D(value[0])
            if isinstance(value[1], Pos2D):  # Pos Pos
                self.lr = value[1]
            else:  # Pos Size
                size = Size2D(value=value[1])
                self.lr = Pos2D(x=self.pos.x + size.width, y=self.pos.y + size.height)
        else:  # x,y,x2,y2
            if len(value) != 4:
                raise ValueError(
                    "Invalid value size, either provide "
                    "((x,y),(width,height)) or (x,y,x2,y2)"
                )
            self.pos = Pos2D(x=value[0], y=value[1])
            self.lr = Pos2D(x=value[2], y=value[3])

    def __str__(self):
        return f"Bounding2D({self.pos.x},{self.pos.y},{self.lr.x},{self.lr.y})"

    def __repr__(self):
        return self.__str__()

    def copy(self) -> Bounding2D:
        """
        Creates a copy of the bounding
        :return: The copy
        """
        return Bounding2D(self)

    def get_size(self) -> Size2D:
        """
        Returns the element's size as Size2D object

        :return: The size in pixels
        """
        return Size2D(width=self.lr.x - self.pos.x, height=self.lr.y - self.pos.y)

    def is_empty(self) -> bool:
        """
        Returns if the bounding is zero

        :return: True if width and height are zero
        """
        return self.lr.x == self.pos.x and self.lr.y == self.pos.y

    def get_size_tuple(self) -> tuple[float, float]:
        """
        Returns the element's size as float tuple

        :return: The size in pixels
        """
        return (self.lr.x - self.pos.x, self.lr.y - self.pos.y)

    def get_int_size_tuple(self) -> tuple[float, float]:
        """
        Returns the element's size as int tuple

        :return: The size in pixels
        """
        return (int(round(self.lr.x - self.pos.x)), int(round(self.lr.y - self.pos.y)))

    def width(self) -> float:
        """
        Returns the element's width

        :return: The width in pixels
        """
        return self.lr.x - self.pos.x

    def height(self) -> float:
        """
        Returns the element's height

        :return: The height in pixels
        """
        return self.lr.y - self.pos.y

    def to_coord_tuple(self) -> (float, float, float, float):
        """
        Returns the bounding as 1D coordinate tuple

        :return: A tuple in the format x, y, x2, y2
        """
        return (self.pos.x, self.pos.y, self.lr.x, self.lr.y)

    def to_int_coord_tuple(self) -> (int, int, int, int):
        """
        Returns the bounding as 1D coordinate tuple

        :return: A tuple in the format x, y, x2, y2
        """
        return (
            int(round(self.pos.x)),
            int(round(self.pos.y)),
            int(round(self.lr.x)),
            int(round(self.lr.y)),
        )

    def to_nested_coord_tuple(self) -> ((float, float), (float, float)):
        """
        Returns the bounding as 1D coordinate tuple

        :return: A tuple in the format (x, y), (x2, y2)
        """
        return (self.pos.x, self.pos.y), (self.lr.x, self.lr.y)

    def to_coord_size_tuple(self) -> (float, float, float, float):
        """
        Returns the bounding as 1D coordinate, width, height tuple

        :return: A tuple in the format x, y, width, height
        """
        return (self.pos.x, self.pos.y, self.lr.x - self.pos.x, self.lr.y - self.pos.y)

    def to_int_coord_size_tuple(self) -> (int, int, int, int):
        """
        Returns the bounding as 1D coordinate, width, height tuple

        :return: A tuple in the format x, y, width, height
        """
        return (
            int(round(self.pos.x)),
            int(round(self.pos.y)),
            int(round(self.lr.x - self.pos.x)),
            int(round(self.lr.y - self.pos.y)),
        )

    def to_nested_coord_size_tuple(self) -> ((float, float), (float, float)):
        """
        Returns the bounding as 1D coordinate, width, height tuple

        :return: A tuple in the format (x, y), (width, height)
        """
        return (self.pos.x, self.pos.y), (
            self.lr.x - self.pos.x,
            self.lr.y - self.pos.y,
        )

    def __eq__(self, other: Bounding2DTypes) -> bool:
        if not isinstance(other, self.__class__):
            other = Bounding2D(other)
        return self.pos == other.pos and self.lr == other.lr

    def __ne__(self, other: Bounding2DTypes) -> bool:
        if not isinstance(other, self.__class__):
            other = Bounding2D(other)
        return self.pos != other.pos or self.lr != other.lr


RawBoundingType = tuple[tuple[float, float], tuple[float, float]]
"""
Defines the raw bounding type with the structure ((x,y),(x2,y2)).
"""

__all__ = ["Bounding2D", "Bounding2DTypes", "RawBoundingType"]
