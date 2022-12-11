from __future__ import annotations

from dataclasses import dataclass
from typing import Union

Pos2DTuple = tuple[float, float]
"A position tuple defined by x and y"
Pos2DTypes = Union["Pos2D", Pos2DTuple]
"""
Type definition for any supported 2D position type. Use Pos2D(value) 
to convert the value automatically.
"""


@dataclass
class Pos2D:
    """
    Defines the position of a 2D element in pixels
    """

    x: float
    "The x component"
    y: float
    "The y component"

    def __init__(
        self,
        value: Pos2DTypes | float | None = None,
        y: float | None = None,
        x: float | None = None,
    ):
        """
        :param value: The new value, either a Pos2D object to copy,
            x or a tuple containing x and y
        :param y: The y coordinate component
        :param x: The x coordinate component

        Example:

        ``Pos2D(15, 14) == Pos2D((15, 14)) == Pos2D(x=15, y=14) ==
        Pos2D(Pos2D(x=15, y=14))``
        """
        if x is not None:
            if y is None:
                raise ValueError("Missing y parameter")
            self.x = float(x)
            self.y = float(y)
            return
        if isinstance(value, (float, int)):
            if y is None:
                raise ValueError("Missing y parameter")
            self.x = float(value)
            self.y = float(y)
            return
        if isinstance(value, Pos2D):
            self.x, self.y = value.x, value.y
        elif isinstance(value, tuple):
            if len(value) != 2:
                raise ValueError("Invalid tuple size")
            self.x = float(value[0])
            self.y = float(value[1])
        else:
            raise ValueError(
                "Incompatible position type. Should either be a Pos2D object or"
                "a tuple of two numbers."
            )

    def __str__(self):
        return f"Pos2D({self.x},{self.y})"

    def __repr__(self):
        return self.__str__()

    def to_tuple(self) -> (float, float):
        """
        Returns the position as tuple

        :return: X, Y
        """
        return self.x, self.y

    def to_int_tuple(self) -> (int, int):
        """
        Returns the position as int tuple

        :return: X, Y
        """
        return int(round(self.x)), int(round(self.y))

    def __eq__(self, other: Pos2DTypes) -> bool:
        if not isinstance(other, self.__class__):
            other = Pos2D(other)
        return self.x == other.x and self.y == other.y

    def __ne__(self, other: Pos2DTypes) -> bool:
        if not isinstance(other, self.__class__):
            other = Pos2D(other)
        return self.x != other.x or self.y != other.y


__all__ = [Pos2D, Pos2DTuple, Pos2DTypes]
