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
    from scistag.vislog.visual_log_builder import LogBuilder


class AlignmentLogger(BuilderExtension):
    """
    Helper class for adjusting the alignment of elements inside the log
    """

    def __init__(self, builder: "LogBuilder"):
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
        else:
            raise ValueError(f"Unknown alignment {hor_align}")
        html = f'<div style="display: flex; justify-content: {hor_align}"><div>'
        self.builder.add_md(html)
        self.builder.add_html(html)
        context = ElementContext(
            self.builder,
            closing_code={"html": "</div></div>", "md": "</div></div>", "txt": ""},
        )
        return context

    @property
    def left(self) -> ElementContext:
        """
        Shortcut for .align("left")

        :return: The context
        """
        return self("left")

    @property
    def right(self) -> ElementContext:
        """
        Shortcut for .align("right")

        :return: The context
        """
        return self("right")

    @property
    def center(self) -> ElementContext:
        """
        Shortcut for .align("center")

        :return: The context
        """
        return self("center")
