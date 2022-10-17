from __future__ import annotations
from typing import Union
from dataclasses import dataclass

ColorTypes = Union["Color", tuple[int, int, int], tuple[int, int, int, int],
                   tuple[float, float, float],
                   tuple[float, float, float, float],
                   str]
"""
The supported color type. Either a Color or a tuple of 3 or 4 
ints or floats (RGB/RGBA)
"""


@dataclass
class Color:
    """
    ImageStag's standard color definition class.

    Stores the channel intensities for red, green, blue and optional alpha
    (the opacity) of this color.
    """

    r: float = 1.0
    "The red color component. 0 .. 1.0"
    g: float = 1.0
    "The green color component. 0 .. 1.0"
    b: float = 1.0
    "The blue color component. 0 .. 1.0"
    a: float = 1.0
    "The alpha color component. (0=completely transparent, 1.0 = 100% opaque)"

    _rgba: tuple = ()
    "Cached float tuple"
    _int_rgba: tuple = ()
    "Cached, rounded int tuple"

    def __init__(self,
                 value: ColorTypes | float | None = None,
                 green=1.0,
                 blue=1.0,
                 alpha=1.0,
                 red: float | None = None):
        """
        Initializer

        :param value: Red (0.0 .. 1.0), a tuple of 3 or 4 floats or integers
            defining the color or a hex code,
            beginning with a # and with either 6 or 8 digits
            (#RRGGBB or #RRGGBBAA).

            Float values are assumed to be in range 0.0 to 1.0.
        :param red: The red color component (0.0 .. 1.0)
        :param green: The green color component (0.0 .. 1.0)
        :param blue: The blue color component (0.0 .. 1.0)
        :param alpha: The alpha value (opacity of the color) (0.0 .. 1.0).
            Not supported by all drawing functions.
            0 .. 1.0. Int value in range 0 .. 255

        Usage:

        ``Color(red=1.0, green=0.0, blue=0.5) == Color(1.0, 0.0, 0.5) ==
         Color((1.0, 0.0, 0.5)) == Color((255, 0, 127))``
        """
        if red is not None:
            value = red
        else:
            if value is None:
                raise ValueError("Missing color initialization data")
        if isinstance(value, Color):
            self.r, self.g, self.b, self.a = \
                value.r, value.g, value.b, value.a
        elif isinstance(value, tuple):
            if len(value) < 2 or len(value) > 4:
                raise ValueError(
                    "Invalid color structure. 3 or 4 values assumed.")
            if isinstance(value[0], float):
                if len(value) == 3:
                    self.r, self.g, self.b = value
                    self.a = 1.0
                else:
                    self.r, self.g, self.b, self.a = value
            else:
                if len(value) == 3:
                    self.r, self.g, self.b = value[0] / 255.0, value[
                        1] / 255.0, value[2] / 255.0
                    self.a = 1.0
                else:
                    self.r, self.g, self.b, self.a = value[0] / 255.0, \
                                                     value[1] / 255.0, \
                                                     value[2] / 255.0, \
                                                     value[
                                                         3] / 255.0,
        elif isinstance(value, str):
            if not value.startswith("#") or (
                    len(value) != 7 and len(value) != 9):
                raise ValueError(
                    "Invalid color definition. Use #RRGGBB or #RRGGBBAA")
            h: str = value.lstrip("#")
            if len(h) == 6:
                values = tuple(int(h[i:i + 2], 16) / 255.0 for i in [0, 2, 4])
                self.r, self.g, self.b = values
                self.a = 1.0
            else:
                values = tuple(
                    int(h[i:i + 2], 16) / 255.0 for i in [0, 2, 4, 6])
                self.r, self.g, self.b, self.a = values
        elif isinstance(value, float):
            self.r = value
            self.g = green
            self.b = blue
            self.a = alpha
        else:
            raise TypeError("Invalid data type")
        self._rgba = (self.r, self.g, self.b, self.a)
        self._int_rgba = tuple(
            [int(round(element * 255.0)) for element in self._rgba])

    def __setattr__(self, key, value):
        if key in {"r", "g", "b", "a", "_rgba", "_int_rgba"} and \
                "_int_rgba" in self.__dict__:
            raise RuntimeError("Modifying a Color is not allowed.")
        else:
            super().__setattr__(key, value)

    def __str__(self) -> str:
        return f"Color({round(self.r, 3)}," \
               f"{round(self.g, 3)}," \
               f"{round(self.b, 3)}," \
               f"{round(self.a, 3)})" if self.a != 1.0 else \
            f"Color({round(self.r, 3)}," \
            f"{round(self.g, 3)}," \
            f"{round(self.b, 3)})"

    def to_rgb(self) -> (float, float, float):
        """
        Returns the color as rgb tuple (values from 0.0 .. 1.0)

        :return: The RGB values
        """
        return tuple(self._rgba[0:3])

    def to_int_rgb(self) -> (int, int, int):
        """
        Returns the color as rgb int tuple (values from 0 .. 255)
        :return: The RGB values
        """
        return self._int_rgba[0:3]

    def to_rgba(self) -> (float, float, float, float):
        """
        Returns the color as rgb tuple (values from 0.0 .. 1.0)

        :return: The RGB values
        """
        return tuple(self._rgba)

    def to_int_rgba(self) -> (int, int, int, int):
        """
        Returns the color as rgb int tuple (values from 0 .. 255)
        :return: The RGB values
        """
        return tuple(self._int_rgba)

    def to_hex(self) -> str:
        """
        Converts the color to it's HTML hex representation, e.g.
        #FF0000 for red, #FFFFFF for white, #000000 for black etc. where
        each of the 3 or 4 color components is encoded into a two digit
        hex string.

        :return: The hex string such as #FF0000 - either 7 digits if
            alpha is 1.0 (255), otherwise 9 digits.
        """
        r, g, b, a = self.to_int_rgba()
        return f'#{r:02X}{g:02X}{b:02X}' if a == 255 \
            else f'#{r:02X}{g:02X}{b:02X}{a:02X}'

    def __eq__(self, other):  # equal
        return self.r == other.r and \
               self.g == other.g and \
               self.b == other.b and \
               self.a == other.a

    def __ne__(self, other):  # not equal
        return self.r != other.r or \
               self.g != other.g or \
               self.b != other.b or \
               self.a != other.a


class Colors:
    """
    Definition of common colors
    """

    BLACK = Color("#000000")
    "Black"
    WHITE = Color("#FFFFFF")
    "White"
    LIGHT_GRAY = Color(red=0.75, green=0.75, blue=0.75)
    "LightGray"
    GRAY = Color(red=0.5, green=0.5, blue=0.5)
    "Gray"
    DARK_GRAY = Color(red=0.25, green=0.25, blue=0.25)
    "DarkGray"
    RED = Color("#FF0000")
    "Red"
    DARK_RED = Color("#8B0000")
    "DarkRed"
    GREEN = Color("#00FF00")
    "Green"
    BLUE = Color("#0000FF")
    "Blue"
    BLUE_VIOLET = Color("#8A2BE2")
    "BlueViolet"
    AQUA = CYAN = Color("#00FFFF")
    "Cyan"
    GOLD = Color("#FFD700")
    "Gold"
    FUCHSIA = MAGENTA = Color("#FF00FF")
    "Fuchsia"
    YELLOW = Color("#FFFF00")
    "Yellow"
    DARK_MAGENTA = Color("#8B008B")
    "DarkMagenta"
    DARK_ORANGE = Color("#FF8C00")
    "DarkOrange"
    TRANSPARENT = Color("#00000000")
    "Transparent"


RawColorType = tuple[int, int, int, int]
"""
Defines a raw color types structure (4 integer values from 0..255), de facto
unsigned bytes but Python anyway doesn't make a difference here.
"""

__all__ = ["Color", "Colors", "ColorTypes", "RawColorType"]
