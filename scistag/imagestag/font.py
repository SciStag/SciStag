"""
Implements the class :class:`Font` which is able to load TrueType fonts from
disk, provides the handle to render a text using PILLOW and functions to
measure text size, align text etc.
"""

from __future__ import annotations

from enum import IntEnum
from io import BytesIO
from typing import Literal, Union

import PIL.ImageFont

from scistag.imagestag import ImsFramework, Bounding2D, Pos2D, Size2D
from .text_alignment_definitions import (
    HTextAlignment,
    VTextAlignment,
    VTextAlignmentTypes,
    HTextAlignmentTypes,
)


class Font:
    """
    SDK independent font handle
    """

    def __init__(
        self, source: str | bytes | BytesIO, size: int, framework: ImsFramework, index=0
    ):
        """
        Initializer
        :param source: The font source. Either a file path, a bytes like object
            or a stream
        :param size: The font's size
        :param framework: The framework to be used
        :param index: The font face index
        """
        self.framework = framework
        "The framework being used to render the font"
        self.size = size
        """
        The font size in pixels as passed in the constructor when creating the
        font. Usually this defines (coarsely) the height of the font above the 
        baseline.
        """
        if isinstance(source, bytes):
            source = BytesIO(source)
        if framework == ImsFramework.PIL:
            self._font_handle = PIL.ImageFont.truetype(
                source, size, index=index, layout_engine=PIL.ImageFont.Layout.BASIC
            )
        else:
            self._font_handle = None
            raise NotImplementedError("At the moment only PIL fonts are supported.")
        metrics = self._font_handle.getmetrics()
        self.ascend = int(round(metrics[0]))
        "The maximum size of a character above the baseline (in pixels)"
        self.descend = int(abs(round(metrics[1])))
        "The maximum size of a character below the baseline (in pixels)"
        self.row_height = self.ascend + self.descend
        """
        The real size of the font in pixels, assuming characters with large
        ascends such as German umlauts and descending characters. This is the
        height a text printed with this font will cover at max. 
        """
        self._y_start_offsets = {
            VTextAlignment.TOP: 0,
            VTextAlignment.BOTTOM: -self.row_height,
            VTextAlignment.CENTER: -self.ascend // 2,
            VTextAlignment.REAL_CENTER: -self.row_height // 2,
            VTextAlignment.BASELINE: -self.ascend,
        }
        """
        Dictionary for converting a vertical alignment to a relative y
        starting offset
        """

    def get_handle(self) -> PIL.ImageFont.FreeTypeFont:
        """
        Returns the low level font handle
        :return: The font handle
        """
        return self._font_handle

    def get_y_offset(self, vert_alignment: VTextAlignmentTypes):
        """
        Returns the relative y starting offset for given vertical alignment
        type.

        :param: vert_alignment: The vertical alignment
        :return: The y shifting relative to a top-left starting point in pixels.
        """
        vert_alignment = VTextAlignment(vert_alignment)
        return self._y_start_offsets[vert_alignment]

    def get_text_size(
        self,
        text: str,
        out_lines: list[str] | None = None,
        out_widths: list[int] | None = None,
    ) -> Size2D:
        """
        Returns the text size in pixels

        :param text: The text of which the size shall be determined
        :param out_lines: If provided it receives the single lines of the text
        :param out_widths: If provided it receives the widths of the single
            lines.
        :return: The size in pixels
        """
        if out_lines is not None:
            out_lines.clear()
            out_lines += text.split("\n")
            lines = out_lines
        else:
            lines = text.split("\n")
        if out_widths is not None:
            out_widths.clear()
        width = 0
        for row in lines:
            cur_width = self._font_handle.getbbox(row)[2]
            if out_widths is not None:
                out_widths.append(cur_width)
            width = max(cur_width, width)
        return Size2D(width, len(lines) * self.row_height)

    def get_covered_area(
        self,
        text: str,
        h_align: HTextAlignmentTypes = HTextAlignment.LEFT,
        v_align: VTextAlignmentTypes = VTextAlignment.TOP,
    ) -> Bounding2D:
        """
        Returns the area in which this text will modify pixels, relative to
        pos 0,0.

        The bounding box defines the area of the printed text which is covered
        with pixels where the smallest y can be zero and the biggest y2 can
        be :attr:`ascend` + :attr:`descend`.

        :param text: The text to be verified
        :param h_align: The horizontal text alignment
        :param v_align: The vertical text alignment
        :return: The bbox (x,y,x2,y2)
        """
        if isinstance(h_align, str):
            h_align = HTextAlignment(h_align)
        if isinstance(v_align, str):
            v_align = VTextAlignment(v_align)
        y_offset = self._y_start_offsets[v_align]
        bounding = (0, 0, 0, 0)
        lines = text.split("\n")
        if self.framework == ImsFramework.PIL:
            for cur_line in lines:
                cur_box = self._font_handle.getbbox(cur_line)
                x_offset = 0
                if h_align == "center":
                    x_offset = -cur_box[2] // 2
                elif h_align == "right":
                    x_offset = -cur_box[2]
                bounding = (
                    min(cur_box[0] + x_offset, bounding[0]),
                    min(cur_box[1] + y_offset, bounding[1]),
                    max(cur_box[2] + x_offset, bounding[2]),
                    max(cur_box[3] + y_offset, bounding[3]),
                )
                y_offset += self.row_height
            return Bounding2D(bounding)
        raise NotImplementedError("At the moment only PIL fonts are supported.")


__all__ = [Font]
