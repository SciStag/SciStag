"""
Defines AlignmentLogger which allows aligning objects within the log
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from scistag.vislog.common.element_context import ElementContext
from scistag.vislog.extensions.builder_extension import BuilderExtension

HORIZONTAL_ALIGNMENTS = Literal["left", "center", "right", "l", "c", "r"]
"Definition of different horizontal alignments"

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import VisualLogBuilder


class AlignmentLogger(BuilderExtension):
    """
    Helper class for adjusting the alignment of elements inside the log
    """

    def __init__(self, builder: "VisualLogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)
        self.show = self.__call__

    def __call__(
            self, hor_align: HORIZONTAL_ALIGNMENTS | None = None
    ) -> ElementContext:
        """
        Horizontally aligns the element

        :param hor_align: The horizontal alignment
        :return: The alignment context
        """
        if hor_align is None:
            hor_align = "left"
        if hor_align.startswith("l"):
            hor_align = "left"
        elif hor_align.startswith("c"):
            hor_align = "center"
        elif hor_align.startswith("r"):
            hor_align = "right"
        self.builder.add_md(f'<div style="text-align:{hor_align};">')
        self.builder.add_html(f'<div style="text-align:{hor_align};">')
        context = ElementContext(
            self.builder, closing_code={"html": "</div>", "md": "</div>", "txt": ""}
        )
        return context

    def left(self) -> ElementContext:
        """
        Shortcut for .align("left")

        :return: The context
        """
        return self("left")

    def right(self) -> ElementContext:
        """
        Shortcut for .align("right")

        :return: The context
        """
        return self("right")

    def center(self) -> ElementContext:
        """
        Shortcut for .align("center")

        :return: The context
        """
        return self("center")
