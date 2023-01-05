"""
Implements the AsciiImage class which converts an image to ASCII using
different methods
"""
from __future__ import annotations

import os.path
from enum import IntEnum

import numpy as np

from scistag.filestag import FileStag
from scistag.imagestag import Color, Colors
from scistag.imagestag.image import Image

CHARACTERS_GRAY_LEVELS_10 = "@%#*+=-:. "[::-1]
"ASCII representation with 10 nuances"

CHARACTERS_GRAY_LEVELS_13 = "BS#&@$%*!:. "[::-1]
"Alternate ASCII representation with 10 nuances"

CHARACTERS_GRAY_LEVELS_69 = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft" \
                            "/|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1]
"Alternate ASCII representation with 69 nuances"

TERMINAL_COLORS = FileStag.load_json(
    os.path.dirname(__file__) + "./terminal_colors.json")
"""Definition of the Xterm terminal colors"""


class AsciiImageMethod(IntEnum):
    """
    Defines the method which is used to convert an image to gray scale
    """

    GRAY_LEVELS_13 = 0
    """
    Use grayscale conversions and 13 different levels of gray
    """
    GRAY_LEVELS_10 = 1
    """
    Use grayscale conversion with 10 different levels of gray
    """
    GRAY_LEVELS_69 = 2
    """
    Use grayscale conversion with 69 different levels of gray
    """
    COLOR_ASCII = 3
    """
    Convert to color ASCII using escape codes
    """


class AsciiImage:
    """
    Helper class for converting images from RGB to ASCII, e.g. for being
    able to add images to text-only logs and to provide at least a coarse
    "preview" of the real image.
    """

    def __init__(
            self,
            image: Image,
            method: AsciiImageMethod = AsciiImageMethod.COLOR_ASCII,
            max_width=80,
            **params,
    ):
        """
        :param image: The input image
        :param max_width: The maximum characters per row
        :param params: Advanced parameters
        """
        self.image = image
        "The image to be converted"
        self.max_width = max_width
        "The maximum character count per row"
        self.ascii_image: str = ""
        "The ASCII representation of the image after it's conversion"
        self.scaled_image: Image | None = None
        "The scaled image"
        self.is_converted = False
        "Defines if the conversion was executed already"
        self.method = method
        """The conversion method to use"""
        # self.dictionary = GRAY_LEVELS_10_2
        dict_conv = {AsciiImageMethod.GRAY_LEVELS_10: CHARACTERS_GRAY_LEVELS_10,
                     AsciiImageMethod.GRAY_LEVELS_13: CHARACTERS_GRAY_LEVELS_13,
                     AsciiImageMethod.GRAY_LEVELS_69: CHARACTERS_GRAY_LEVELS_69,
                     AsciiImageMethod.COLOR_ASCII: None
                     }
        self.dictionary = dict_conv[method]
        "The conversion dictionary to use"

    def convert(self) -> AsciiImage:
        """
        Converts the whole image from pixles to ASCII characters

        :return: Self
        """
        width_scaling = self.max_width / self.image.width
        height_scaling = width_scaling / 2
        self.scaled_image = self.image.resized_ext(
            factor=(width_scaling, height_scaling)
        )
        self.scaled_image.convert("rgb", bg_fill=Colors.BLACK)

        if self.method == AsciiImageMethod.COLOR_ASCII:
            self.create_color_ascii()
            return self
        pixels = self.scaled_image.get_pixels_gray()
        self.ascii_image = "\n".join([self.convert_row(row) for row in pixels])
        self.is_converted = True
        return self

    def create_color_ascii(self):
        """
        Creates a color ASCII representation
        """
        pixels = self.scaled_image.get_pixels_rgb()
        out_rows = []
        for row in pixels:
            cur_row = ""
            for col in row:
                r, g, b = tuple(col)
                if int(r) + g + b <= 5:
                    cur_row += " "
                    continue
                cur_row += f"\N{ESC}[38;2;{r};{g};{b}m@"
            out_rows.append(cur_row)
        self.ascii_image = "\n".join(out_rows) + f"\N{ESC}[0m"
        self.is_converted = True

    def convert_row(self, pixels: np.ndarray) -> str:
        """
        Converts a single row from pixels to characters

        :param pixels: The pixel data
        :return: The characters
        """
        ascd = self.dictionary
        factor = (len(ascd) - 1) / 255
        result = "".join([ascd[int(pixel * factor)] for pixel in pixels])
        return result

    def get_ascii(self) -> str:
        """
        Returns the converted image
        :return:
        """
        if not self.is_converted:
            self.convert()
        return self.ascii_image

    def __str__(self):
        return self.get_ascii()
