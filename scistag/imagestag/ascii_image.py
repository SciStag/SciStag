"""
Implements the AsciiImage class which converts an image to ASCII using
different methods
"""
from __future__ import annotations

from enum import IntEnum

import numpy as np

from scistag.imagestag.image import Image

CHARACTERS_GRAY_LEVELS_10 = '@%#*+=-:. '
"ASCII representation with 10 nuances"

CHARACTERS_GRAY_LEVELS_13 = "BS#&@$%*!:. "
"Alternate ASCII representation with 10 nuances"


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


class AsciiImage:
    """
    Helper class for converting images from RGB to ASCII, e.g. for being
    able to add images to text-only logs and to provide at least a coarse
    "preview" of the real image.
    """

    def __init__(self, image: Image,
                 method: AsciiImageMethod = AsciiImageMethod.GRAY_LEVELS_10,
                 max_width=80, **params):
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
        # self.dictionary = GRAY_LEVELS_10_2
        self.dictionary = CHARACTERS_GRAY_LEVELS_10 \
            if method == CHARACTERS_GRAY_LEVELS_10 \
            else CHARACTERS_GRAY_LEVELS_10
        "The conversion dictionary to use"

    def convert(self) -> AsciiImage:
        """
        Converts the whole image from pixles to ASCII characters

        :return: Self
        """
        width_scaling = self.max_width / self.image.width
        height_scaling = width_scaling / 2
        self.scaled_image = \
            self.image.resized_ext(factor=(width_scaling, height_scaling))
        pixels = self.scaled_image.get_pixels_gray()
        self.ascii_image = \
            "\n".join([
                self.convert_row(row) for row in pixels
            ])
        self.is_converted = True
        return self

    def convert_row(self, pixels: np.ndarray) -> str:
        """
        Converts a single row from pixels to characters

        :param pixels: The pixel data
        :return: The characters
        """
        # return ''.join([GRAY_LEVELS_10_2[pixel // 25] for pixel in pixels])
        ascd = self.dictionary
        factor = (len(ascd) - 1) / 255
        return ''.join([ascd[int(pixel * factor)] for pixel in pixels])

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
