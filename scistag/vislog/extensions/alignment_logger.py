"""
Defines AlignmentLogger which allows aligning objects within the log
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from scistag.vislog.common.element_context import ElementContext
from scistag.vislog.extensions.builder_extension import BuilderExtension

HORIZONTAL_ALIGNMENTS = Literal[
    "left",
    "center",
    "right",
    "l",
    "c",
    "r",
    "left_block",
    "center_block",
    "right_block",
    "lb",
    "cb",
    "rb",
]
"Definition of different horizontal alignments"

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import LogBuilder


class AlignmentContext(ElementContext):
    """
    A context which keeps track of the current alignment of text and block elements
    """

    def __init__(self, state: str, block: bool = False, **kwargs):
        """
        :param state: The new alignment state, either, left, center or right
        :param block: Defines if this alignment is a block or text alignment
        """
        super().__init__(**kwargs)
        self.state = state
        self.previous_state = ""
        self.block = block

    def __enter__(self):
        if self.block:
            self.previous_state = self.builder._cur_alignment_block
            self.builder._cur_alignment_block = self.state
        else:
            self.previous_state = self.builder._cur_alignment
            self.builder._cur_alignment = self.state
        result = super().__enter__()
        return result

    def __exit__(self, *args, **kwargs):
        if self.block:
            self.builder._cur_alignment_block = self.previous_state
        else:
            self.builder._cur_alignment = self.previous_state
        super().__exit__(*args, **kwargs)


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

        block = (
            len(hor_align) == 2
            and hor_align.endswith("b")
            or hor_align.endswith("_block")
        )

        if hor_align.startswith("l"):
            hor_align = "left"
        elif hor_align.startswith("c"):
            hor_align = "center"
        elif hor_align.startswith("r"):
            hor_align = "right"
        else:
            raise ValueError(f"Unknown alignment {hor_align}")

        md_html = self.builder.md.html_only

        if block:
            html = f'<div style="display: flex; justify-content: {hor_align}"><div>'
            if md_html:
                self.builder.add_md(html)
            self.builder.add_html(html)
            context = AlignmentContext(
                block=block,
                state=hor_align,
                builder=self.builder,
                closing_code={
                    "html": "</div></div>",
                    "md": "</div></div>" if md_html else "",
                    "txt": "",
                },
            )
            return context
        else:
            html = f'<div style="text-align: {hor_align}">'
            if md_html:
                self.builder.add_md(html)
            self.builder.add_html(html)
            context = AlignmentContext(
                block=block,
                state=hor_align,
                builder=self.builder,
                closing_code={
                    "html": "</div>",
                    "md": "</div>" if md_html else "",
                    "txt": "",
                },
            )
            return context

    @property
    def left(self) -> ElementContext:
        """
        Aligns text and images to the left.

        Note: Does NOT align elements such as tables or widget groups, see
        :meth:`left_block` for such.

        Shortcut for .align("left")

        :return: The context
        """
        return self("left")

    @property
    def right(self) -> ElementContext:
        """
        Aligns text and images to the right.

        Note: Does NOT align elements such as tables or widget groups, see
        :meth:`right_block` for such.

        Shortcut for .align("right")

        :return: The context
        """
        return self("right")

    @property
    def center(self) -> ElementContext:
        """
        Aligns text and images to the center.

        Note: Does NOT align elements such as tables or widget groups, see
        :meth:`center_block` for such.

        :return: The context
        """
        return self("center")

    @property
    def block_left(self) -> ElementContext:
        """
        Creates a block surrounding the content created in this context and aligns
        it to the left.

        Shortcut for .align("left_block")

        :return: The context
        """
        return self("center_left")

    @property
    def block_right(self) -> ElementContext:
        """
        Creates a block surrounding the content created in this context and aligns
        it to the right.

        Shortcut for .align("right_block")

        :return: The context
        """
        return self("right_block")

    @property
    def block_center(self) -> ElementContext:
        """
        Creates a block surrounding the content created in this context and aligns
        it to the center.

        Shortcut for .align("center_block")

        :return: The context
        """
        return self("center_block")
