"""
Implements the :class:`FormattedText` class which helps formatting and
printing multiline text.
"""

from __future__ import annotations

from scistag.imagestag import Font, HTextAlignment, VTextAlignment, Pos2D


class FormattedText:
    """
    Helper class which helps printing and aligning multi-line and
    in the future also multi-format texts.
    """

    def __init__(
        self,
        text: str,
        font: Font,
        h_align: HTextAlignment = HTextAlignment.LEFT,
        v_align: VTextAlignment = VTextAlignment.TOP,
        line_spacing: int = 0,
    ):
        """
        :param text: The text to be verified
        :param font: The font to be used
        :param h_align: The horizontal text alignment
        :param v_align: The vertical text alignment
        :param line_spacing: Defines the additional space between each line
            in pixels.
        """
        self.text_elements = text.split("\n")
        if len(self.text_elements) == 0:
            self.text_elements = [""]
        "The single text elements"
        self.font = font
        "The font to be used"
        font_handle = font.get_handle()
        self.line_spacing = line_spacing
        "The additional space between each line in pixels"
        self.element_widths = [
            font_handle.getbbox(element)[2] for element in self.text_elements
        ]
        "Contains the width of every single text element"
        self.width = width = max(self.element_widths)
        "The text's width in pixels"
        half_width = width // 2
        "The text width"
        self.height = font.row_height * len(self.text_elements)
        "The text's height in pixels"
        y_offset = self.font.get_y_offset(v_align)
        self.text_positions = []
        "The position (relative to the starting point) of each line"
        self.y_offsets = []
        "The y offset for each row"
        for index, row in enumerate(self.text_elements):
            if h_align == HTextAlignment.LEFT:
                x_offset = 0.0
            elif h_align == HTextAlignment.CENTER:
                x_offset = half_width // 2 - self.element_widths[index] // 2
            else:
                x_offset = width - self.element_widths[index]
            self.text_positions.append(Pos2D(x_offset, y_offset))
            y_offset += self.font.row_height
            self.y_offsets.append(y_offset)
