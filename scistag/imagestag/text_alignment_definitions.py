"""
Defines the text alignment types
"""

from __future__ import annotations

from enum import IntEnum
from typing import Union, Literal


class HTextAlignment(IntEnum):
    """
    Defines the horizontal text alignment
    """

    LEFT = 0
    "Text is written to the right of ax x starting point"
    CENTER = 1
    "Text is written to the left of an x starting point"
    RIGHT = 2
    "Text is centered equally to the left and right of an x starting point"

    @classmethod
    def _missing_(cls, value: str) -> int:
        """
        Returns the value for given short code

        :param value: Either an alignment to copy or one of the following
            string codes:
            - "l" / "left" for LEFT aligned text
            - "c" / "center" for CENTERED text
            - "r" / "right" for RIGHT aligned text
        :return: The enum for value representing the code provided
        """

        class Definitions:
            short_codes = {"l": HTextAlignment.LEFT,
                           "c": HTextAlignment.CENTER,
                           "r": HTextAlignment.RIGHT,
                           "left": HTextAlignment.LEFT,
                           "center": HTextAlignment.CENTER,
                           "right": HTextAlignment.RIGHT}

        if value not in Definitions.short_codes:
            raise ValueError("Unknown horizontal alignment shortcode."
                             "Valid codes are l, c, r, left, center, right")
        return Definitions.short_codes[value]


HTextAlignmentLiterals = Literal["l", "c", "r", "left", "center", "right"]
"Literal alternative for passing a horizontal text alignment"
HTextAlignmentTypes = Union[HTextAlignment, HTextAlignmentLiterals]
"Type definition of ways to define a horizontal text alignment"


class VTextAlignment(IntEnum):
    """
    Defines the vertical placement of a text (line-wise)

    Note that you can not center a multi-line text using a vertical alignment.

    If you want to center multi-line text use the anchor parameter of the
    drawing function and use a "top" vertical alignment for the printing.

    See :class:`RegionAnchor`.
    """

    TOP = 0
    "Text is written to the bottom of a y starting point"
    CENTER = 1
    """
    Text is (line-wise) centered relative to a y starting point 
    around it's ascending size span (with no respect to descending characters).
    This in many cases looks more natural, especially when just upper case
    characters or dashes are being used.   
    """
    REAL_CENTER = 2
    """
    Text is (line-wise) centered relative to a y starting point
    around it's full size span.    
    """
    BASELINE = 3
    """
    Text is printed relative to it's baseline ("on top of this 
    baseline) where the y then equals the low left pixel of a non-descending 
    character such as an x.    
    """
    BOTTOM = 4
    """
    Text is printed to the top of a y starting point with it's full
    height - so no pixel will be below the defined starting point.    
    """

    @classmethod
    def _missing_(cls, value: str) -> int:
        """
        Returns a value from a short code

        :param value: Either an alignment to copy or one of the following
            string codes:
            - "t" / "top" for TOP aligned text
            - "c" / "center" for CENTERED text (centered on ascend)
            - "rc" / "realCenter" for REAL_CENTER text (centered on row height)
            - "b" / "bottom" for bottom aligned text
            - "bl" / "baseline" for text aligned on the baseline
        :return: The corresponding enum value
        """

        class Definitions:
            short_codes = {"t": VTextAlignment.TOP,
                           "c": VTextAlignment.CENTER,
                           "rc": VTextAlignment.REAL_CENTER,
                           "b": VTextAlignment.BOTTOM,
                           "bl": VTextAlignment.BASELINE,
                           "top": VTextAlignment.TOP,
                           "center": VTextAlignment.CENTER,
                           "realCenter": VTextAlignment.REAL_CENTER,
                           "bottom": VTextAlignment.BOTTOM,
                           "baseline": VTextAlignment.BASELINE}

        if value not in Definitions.short_codes:
            raise ValueError("Unknown vertical alignment shortcode."
                             "Valid codes are t, c, b, rc, bl,"
                             "top, center, realCenter, bottom and "
                             "baseline")
        return Definitions.short_codes[value]


VTextAlignmentLiterals = Literal["t", "c", "rc", "b", "bl", "top", "center",
                                 "realCenter", "bottom", "baseLine"]
"Literal alternative for passing a vertical text alignment"
VTextAlignmentTypes = Union[VTextAlignment, VTextAlignmentLiterals]
"Type definition of ways to define a vertical text alignment"
