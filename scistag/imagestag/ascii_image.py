"""
Implements the AsciiImage class which converts an image to ASCII using
different methods
"""
from __future__ import annotations

import os.path
import time
from enum import IntEnum

import numpy as np

from scistag.filestag import FileStag
from scistag.imagestag import Color, Colors
from scistag.imagestag.image import Image

CHARACTERS_GRAY_LEVELS_10 = "@%#*+=-:. "[::-1]
"ASCII representation with 10 nuances"

CHARACTERS_GRAY_LEVELS_13 = "BS#&@$%*!:. "[::-1]
"Alternate ASCII representation with 10 nuances"

CHARACTERS_GRAY_LEVELS_69 = (
    "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft" "/|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1]
)
"Alternate ASCII representation with 69 nuances"

TERMINAL_COLORS = FileStag.load_json(
    os.path.dirname(__file__) + "./terminal_colors.json"
)
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
        method: AsciiImageMethod = AsciiImageMethod.GRAY_LEVELS_69,
        max_columns=80,
        min_columns=None,
        align: str = "left",
        **params,
    ):
        """
        :param image: The input image
        :param min_columns: The minimum width in pixels
        :param max_columns: The maximum characters per row
        :param params: Advanced parameters
        """
        self.image = image
        "The image to be converted"
        self.max_columns = int(max_columns)
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
        dict_conv = {
            AsciiImageMethod.GRAY_LEVELS_10: CHARACTERS_GRAY_LEVELS_10,
            AsciiImageMethod.GRAY_LEVELS_13: CHARACTERS_GRAY_LEVELS_13,
            AsciiImageMethod.GRAY_LEVELS_69: CHARACTERS_GRAY_LEVELS_69,
            AsciiImageMethod.COLOR_ASCII: None,
        }
        self.dictionary = dict_conv[method]
        "The conversion dictionary to use"
        self.min_columns = min_columns
        "The minimum width of the output image, e.g. to center or right align it"
        self.alignment = align
        'The text alignment, either "left", "center" or "right"'

    def convert(self) -> AsciiImage:
        """
        Converts the whole image from pixles to ASCII characters

        :return: Self
        """
        width_scaling = self.max_columns / self.image.width
        height_scaling = width_scaling / 2
        self.scaled_image = self.image.resized_ext(
            factor=(width_scaling, height_scaling)
        )

        if self.method == AsciiImageMethod.COLOR_ASCII:
            if self.scaled_image.pixel_format.band_count < 3:
                self.scaled_image.convert("rgb")
            rows = self.create_color_ascii()
        else:
            self.scaled_image.convert("rgb", bg_fill=Colors.BLACK)
            pixels = self.scaled_image.get_pixels_gray()
            rows = [self.convert_row(row) for row in pixels]
        self.is_converted = True
        if self.min_columns is not None and self.alignment != "left":
            missing = self.min_columns - self.max_columns
            if self.alignment == "center":
                missing = missing // 2
            missing = " " * missing
            rows = [missing + row for row in rows]
        self.ascii_image = "\n".join(rows)

        return self

    def create_color_ascii(self):
        """
        Creates a color ASCII representation
        """
        pixels = self.scaled_image.pixels
        if pixels.shape[2] == 4:
            self.scaled_image.convert("rgb", bg_fill=Colors.BLACK)
        rgb_pixels = self.scaled_image.pixels
        if pixels.shape[2] == 4:
            out_rows = []
            for row, a_row in zip(rgb_pixels, pixels):
                elements = [
                    f"\N{ESC}[38;2;{col[0]};{col[1]};{col[2]}m█" if acol[3] > 5 else " "
                    for col, acol in zip(row, a_row)
                ]
                cur_row = "".join(elements)
                out_rows.append(cur_row)
        else:
            out_rows = []
            for row in rgb_pixels:
                elements = [
                    f"\N{ESC}[38;2;{col[0]};{col[1]};{col[2]}m█"
                    if sum(col) >= 10
                    else " "
                    for col in row
                ]
                cur_row = "".join(elements)
                out_rows.append(cur_row)
        out_rows[-1] += f"\N{ESC}[0m"
        return out_rows

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
