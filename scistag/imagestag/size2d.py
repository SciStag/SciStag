"""
Implements the :class:`Size2D` class which is used to define the horizontal
and vertical size of images and geometries with floating point precision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

Size2DTuple = tuple[float, float]
"A size tuple defined by width and height"
Size2DIntTuple = tuple[int, int]
"A size tuple defined by width and height"
Size2DTypes = Union[Size2DTuple, Size2DIntTuple, "Size2D"]
"""
Type definition for any supported 2D size type. Use Size2D(value) to convert 
the value automatically
"""


@dataclass
class Size2D:
    """
    Defines the size of a 2D element in pixels
    """

    width: float
    "The width in pixels"
    height: float
    "The height in pixels"

    def __init__(
        self,
        value: Size2DTypes | float | None = None,
        height: float | None = None,
        width: float | None = None,
    ):
        """
        :param value: The initial width and height as tuple, a Size2D object
        or the width.
        :param height: The height
        :param width: The width

        Example:

        ``Size2D(50,100) == Size2D(width=50, height=100) == Size2D((50,100)) ==
         Size2D(Size2D(50,100))``
        """
        if width is not None:
            if height is None:
                raise ValueError("Missing height parameter")
            self.width = float(width)
            self.height = float(height)
            return
        if isinstance(value, (float, int)):
            if height is None:
                raise ValueError("Missing height parameter")
            self.width = float(value)
            self.height = float(height)
            return
        if isinstance(value, Size2D):
            self.width, self.height = value.width, value.height
        elif isinstance(value, tuple):
            if len(value) != 2:
                raise ValueError("Invalid tuple size")
            self.width = float(value[0])
            self.height = float(value[1])
        elif value is None:
            self.width = self.height = 0.0
        else:
            raise TypeError("Incompatible data type")

    def __str__(self):
        return f"Size2D({self.width},{self.height})"

    def __repr__(self):
        return self.__str__()

    def is_empty(self) -> bool:
        """
        Returns if the size is zero

        :return: True if width and height are zero
        """
        return self.width == 0.0 and self.height == 0.0

    def to_tuple(self) -> (float, float):
        """
        Returns the size as tuple

        :return: Width, Height
        """
        return self.width, self.height

    def to_int_tuple(self) -> (float, float):
        """
        Returns the size as int tuple

        :return: Width, Height
        """
        return int(round(self.width)), int(round(self.height))

    def __eq__(self, other: Size2DTypes) -> bool:
        if not isinstance(other, self.__class__):
            other = Size2D(other)
        return self.width == other.width and self.height == other.height

    def __ne__(self, other: Size2DTypes) -> bool:
        if not isinstance(other, self.__class__):
            other = Size2D(other)
        return self.width != other.width or self.height != other.height


__alL__ = [Size2D, Size2DTypes, Size2DTuple]
