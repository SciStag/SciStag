"""
Implements the helper class ColorStyleContext as extension of StyleContext which
allows the easy selection of fore and background color
"""

from typing import TYPE_CHECKING

from scistag.vislog.common.element_context import ElementContext

if TYPE_CHECKING:
    from scistag.vislog import LogBuilder


class ColorStyleContext:
    """
    Helper class to create a font context
    """

    def __init__(self, builder: "LogBuilder", background: bool = False):
        """
        :param builder: The log builder
        """
        self.builder = builder
        self._bg = background
        self._style_tag = "background-color" if background else "color"

    def __call__(self, name: str) -> ElementContext:
        """
        Returns a color context within which all text is written using the defined color

        :param name: The color's name or hex code such as "red" or "#FF0000"
        :return: The context
        """
        html = f' <span style="{self._style_tag}: {name}">'
        html_closing = "</span>"
        return ElementContext(
            builder=self.builder,
            opening_code={
                "html": html,
                "md": "",
            },
            closing_code={
                "html": html_closing,
                "md": "",
            },
        )

    @property
    def default(self) -> ElementContext:
        """
        Returns a context for the default color
        """
        if self._bg:
            html = f' <span style="background-color: transparent;">'
        else:
            html = f' <span class="vl_default_color">'
        html_closing = "</span>"
        return ElementContext(
            builder=self.builder,
            opening_code={
                "html": html,
                "md": "",
            },
            closing_code={
                "html": html_closing,
                "md": "",
            },
        )
