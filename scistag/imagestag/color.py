from __future__ import annotations

import typing
from typing import Union
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from scistag.imagestag import PixelFormat

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
                 value: ColorTypes | float | int | None = None,
                 green: float | int = 1.0,
                 blue: float | int = 1.0,
                 alpha: float | int = 1.0,
                 red: float | int | None = None):
        """
        Usage:

        ..  code-block: python

            red = Color(255,0,0)  # red
            red = Color(1.0,0,0)  # red as well
            red = Color((1.0,0.0,0.0))  # guess what
            red = Color((255,0,0))  # guess what
            red = Color("#FF0000")  # guess what
            transparent_blue = Color("#0000FFAA")
            transparent_blue = Color(0.0, 0.0 ,0.0, 0.5)

            Important: When passing the color components as single values
            the data type of the red component decides whether green, red
            and alpha need to be converted from int to float or not, so if
            red (or value) are an int then green and blue will also
            be converted and are assumed to be integer as well.

            Alpha though (which is regularly not passed) is tested separately
            and can always be a float, so something like
            Color(255, 0, 255, 0.5) is valid.

        :param value: One of
            * The red color component (0.0 .. 1.0) or from (0 .. 255)
            * a tuple of 3 or 4 floats or integers (0 .. 1.0 or 0 .. 255)
            * A string defining the color or a hex code,
              beginning with a # and with either 6 or 8 digits
              (#RRGGBB or #RRGGBBAA).

            Float values are assumed to be in range 0.0 to 1.0.
        :param red: The red color component (0.0 .. 1.0 or 0 .. 255)
        :param green: The green color component (0.0 .. 1.0 or 0 .. 255)
        :param blue: The blue color component (0.0 .. 1.0 or 0 .. 255)
        :param alpha: The alpha value (opacity of the color) (0.0 .. 1.0 or
            0 .. 255).

            Alpha is not supported by all drawing functions.
            0 .. 1.0. Int value in range 0 .. 255
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
        elif isinstance(value, int):
            self.r = value / 255.0
            self.g = green / 255.0
            self.b = blue / 255.0
            self.a = alpha / 255.0 if isinstance(alpha, int) else alpha
        else:
            raise TypeError("Invalid data type")
        self._rgba = (self.r, self.g, self.b, self.a)
        self._int_rgba = tuple(
            [int(round(element * 255.0)) for element in self._rgba])

    _HSV_TO_RGB_MAP = {
        0: lambda p, q, t, v: Color(v, t, p),
        1: lambda p, q, t, v: Color(q, v, p),
        2: lambda p, q, t, v: Color(p, v, t),
        3: lambda p, q, t, v: Color(p, q, v),
        4: lambda p, q, t, v: Color(t, p, v),
        5: lambda p, q, t, v: Color(v, p, q)
    }
    """
    Hash hap for converting HSV to RGB 
    """

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float) -> Color:
        """
        Creates a Color from hue, saturation and value (HSV)

        :param h: The hue, so the degree on the "color circle" from 0 .. 360
        :param s: The saturation in percent (0 .. 1.0)
        :param v: The value in percent (0 .. 1.0)
        :return: The Color (RGB) representation
        """
        h /= 360.0
        if s == 0.0:
            return Color(v, v, v)
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p, q, t = (int(255 * (v * (1. - s))),
                   int(255 * (v * (1. - s * f))),
                   int(255 * (v * (1. - s * (1. - f)))))
        v *= 255
        i %= 6
        return cls._HSV_TO_RGB_MAP[i](p, q, t, v)

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
        Returns the color as rgba tuple (values from 0.0 .. 1.0)

        :return: The RGBA values
        """
        return tuple(self._rgba)

    def to_int_rgba(self) -> (int, int, int, int):
        """
        Returns the color as rgba int tuple (values from 0 .. 255)

        :return: The RGBA values
        """
        return tuple(self._int_rgba)

    def to_int_bgra(self) -> (int, int, int, int):
        """
        Returns the color as bgra int tuple (values from 0 .. 255)

        :return: The BGRA values
        """
        return (self._int_rgba[2], self._int_rgba[1], self._int_rgba[0],
                self._int_rgba[3])

    def to_int_bgr(self) -> (int, int, int):
        """
        Returns the color as bgr int tuple (values from 0 .. 255)

        :return: The BGR values
        """
        return self._int_rgba[2], self._int_rgba[1], self._int_rgba[0]

    def to_gray(self) -> float:
        """
        Returns the color as int gray value (0..1.0)

        :return: The gray value (0 .. 1.0)
        """
        return min(max(0.299 * self.r + 0.587 * self.g + 0.114 * self.b, 0.0),
                   1.0)  # convert to gray and clip between 0.0 and 1.0

    def to_int_gray(self) -> int:
        """
        Returns the color as int gray value (0..255)

        :return: The gray value (0 .. 255)
        """
        gray = min(max(0.299 * self.r + 0.587 * self.g + 0.114 * self.b, 0.0),
                   1.0)  # convert to gray and clip between 0.0 and 1.0
        return int(round(gray * 255))

    def to_hsv(self) -> (float, float, float):
        """
        Converts the RGB color components to hue, saturation and value

        :return: Hue (0..360.0 degree), Saturation (0 .. 1.0), Value (0.. 1.0)
        """
        r, g, b = self.r, self.g, self.b
        max_val = max(r, g, b)  # dominant color component
        min_val = min(r, g, b)  # most undominant color component
        val_range = max_val - min_val
        hue = 0.0
        if max_val == min_val:
            pass
        elif max_val == r:
            hue = (60.0 * ((g - b) / val_range) + 360.0) % 360.0
        elif max_val == g:
            hue = (60.0 * ((b - r) / val_range) + 120.0) % 360.0
        else:  # max_val == b:
            hue = (60.0 * ((r - g) / val_range) + 240.0) % 360.0
        if max_val == 0.0:
            saturation = 0.0
        else:
            saturation = (val_range / max_val)
        value = max_val
        return hue, saturation, value

    def to_int_hsv(self) -> (int, int, int):
        """
        Converts the color to an integer HSV representation.

        We are using the PILLOW definition (0..255, 0..255, 0..255)

        :return: The hue saturation and value as int tuple
        """
        h, s, v = self.to_hsv()
        return int(round(h / 360. * 255)), int(round(s * 255)), int(
            round(v * 255))

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

    def to_format(self, pixel_format: "PixelFormat") -> tuple | int | float:
        """
        Returns the value as representation in the given target pixel format

        :param pixel_format: The format to convert to
        :return: The converted color
        """
        from scistag.imagestag import PixelFormat
        _CONVERSION_METHODS = {
            PixelFormat.RGB: lambda color: color.to_int_rgb(),
            PixelFormat.RGBA: lambda color: color.to_int_rgba(),
            PixelFormat.BGR: lambda color: color.to_int_bgr(),
            PixelFormat.BGRA: lambda color: color.to_int_bgr(),
            PixelFormat.GRAY: lambda color: color.to_int_gray(),
            PixelFormat.HSV: lambda color: color.to_int_hsv()}
        if pixel_format in _CONVERSION_METHODS:
            return _CONVERSION_METHODS[pixel_format](self)
        raise ValueError(f"Unsupported target format {pixel_format}")


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
