"""
Implements the class :class:`PixelFormat` which defines the different pixel
formats supported by an :class:`Image` and it's properties.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Literal, Union

from numpy import uint8


class PixelFormat(IntEnum):
    """
    Enumeration of different pixel formats
    """
    RGB = 0
    "Red Green Blue"
    RGBA = 1
    "Red Green Blue Alpha"
    HSV = 2,
    "Hue Saturation Value"
    BGR = 5
    "Blue Green Red"
    BGRA = 6
    "Blue Green Red Alpha"
    GRAY = 10
    "Grayscale"
    UNSUPPORTED = 99
    "Unsupported format"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        class Definitions:
            short_codes = {"rgb": cls.RGB,
                           "rgba": cls.RGBA,
                           "hsv": cls.HSV,
                           "g": cls.GRAY,
                           "gray": cls.GRAY,
                           "bgr": cls.BGR,
                           "bgra": cls.BGRA}

        if value is None:
            return None
        value: str
        lower_value = value.lower()
        if lower_value in Definitions.short_codes:
            return Definitions.short_codes[lower_value]
        return None

    @classmethod
    def from_pil(cls, pil_format: str):
        """
        Returns a color format definition from PIL to ImageStag

        :param pil_format: The format string such as "rgb"
        :return: The SciStag format
        """

        class Definitions:
            """
            Defines the color format conversion dictionary from PIL to ImageStag
            """
            pil_color_format_mapping = \
                {
                    "rgb": PixelFormat.RGB,
                    "rgba": PixelFormat.RGBA,
                    "hsv": PixelFormat.HSV,
                    "l": PixelFormat.GRAY
                }

        pil_format = pil_format.lower()
        return Definitions.pil_color_format_mapping.get(pil_format,
                                                        cls.UNSUPPORTED)

    def to_pil(self) -> Literal["RGB", "RGBA", "L", "HSV"] | None:
        """
        Returns the corresponding PIL color format
        :return: The PIL format code if a corresponding format exists, NOne
            otherwise
        """

        class Definitions:
            """
            Defines the color format conversion dictionary from PIL to ImageStag
            """
            to_pil_color_format_mapping = \
                {
                    PixelFormat.RGB: "RGB",
                    PixelFormat.RGBA: "RGBA",
                    PixelFormat.GRAY: "L",
                    PixelFormat.HSV: "HSV"
                }

        return Definitions.to_pil_color_format_mapping.get(self, None)

    def get_band_names(self):
        """
        Returns the names of the single bands

        :return: The bands, e.g. ['R', 'G', 'B']
        """

        class Definitions:
            """
            Defines the color format conversion dictionary from PIL to ImageStag
            """
            band_names = \
                {
                    PixelFormat.RGB: "RGB",
                    PixelFormat.RGBA: "RGBA",
                    PixelFormat.GRAY: "G",
                    PixelFormat.HSV: "HSV",
                    PixelFormat.BGR: "BGR",
                    PixelFormat.BGRA: "BGRA"
                }

        band = Definitions.band_names[self]
        return [*band]

    def get_full_band_names(self):
        """
        Returns the (fulL) names of the single bands

        :return: The bands, e.g. ['Red', 'Green', 'Blue']
        """

        class Definitions:
            """
            Defines the color format conversion dictionary from PIL to ImageStag
            """
            band_names = \
                {
                    PixelFormat.RGB: ["Red", "Green", "Blue"],
                    PixelFormat.RGBA: ["Red", "Green", "Blue", "Alpha"],
                    PixelFormat.GRAY: ["Gray"],
                    PixelFormat.HSV: ["Hue", "Saturation", "Value"],
                    PixelFormat.BGR: ["Blue", "Green", "Red"],
                    PixelFormat.BGRA: ["Blue", "Green", "Red", "Alpha"]
                }

        return Definitions.band_names[self]

    @property
    def bands(self) -> int:
        """
        Returns the count of bands this pixel type uses

        :return: The count of bands (channels)
        """

        class Definitions:
            bands = {
                PixelFormat.RGB: 3,
                PixelFormat.BGR: 3,
                PixelFormat.RGBA: 4,
                PixelFormat.BGRA: 4,
                PixelFormat.GRAY: 1
            }

        return Definitions.bands[self]

    @property
    def data_type(self) -> type:
        """
        Returns the data type used for the storage of pixels of this type

        :return: The count of bands (channels)
        """

        class Definitions:
            bands = {
                PixelFormat.RGB: uint8,
                PixelFormat.BGR: uint8,
                PixelFormat.RGBA: uint8,
                PixelFormat.BGRA: uint8,
                PixelFormat.GRAY: uint8
            }

        return Definitions.bands[self]


PixelFormatTypes = Union[
    PixelFormat, Literal["RGB", "RGBA", "BGR", "BGRA", "HSV", "G", "GRAY"]]
"""
Definition of supported ways to define a pixel format, either as string or
as PixelFormat"
"""
