"""
Implements FontStyleContext which extends StyleContext for the easy selection of a
font, size and weight. Provides stacks of common default fonts.
"""

from __future__ import annotations

from scistag.vislog import LogBuilder
from scistag.vislog.common.element_context import ElementContext


class FontStyleContext:
    """
    Helper class to create a font context
    """

    _ARIAL_STACK = 'Arial, "Helvetica Neue", Helvetica, sans-serif'
    "Definition of fonts of the Arial font stack and its fallbacks"

    _TREBUCHET = '"Trebuchet MS", "Lucida Grande", "Lucida Sans Unicode", "Lucida Sans", Tahoma, sans-serif;'
    "Definition of fonts of the Trebuchet font stack and its fallbacks"

    _TIMES = 'TimesNewRoman, "Times New Roman", Times, Baskerville, Georgia, serif'
    "Definition of fonts of the Times New Roman font stack and its fallbacks"

    _COURIER = '"Courier New", Courier, "Lucida Sans Typewriter", "Lucida Typewriter", monospace'
    "Definition of fonts of the Courier font stack and its fallbacks"

    _LUCIDA = '"Lucida Sans Typewriter", "Lucida Console", monaco, "Bitstream Vera Sans Mono", monospace'
    "Definition of fonts of the Lucida font stack and its fallbacks"

    _GEORGIA = 'Georgia, Times, "Times New Roman", serif;'
    "Definition of fonts of the Georgia font stack and its fallbacks"

    _TAHOMA = "Tahoma, Verdana, Segoe, sans-serif"
    "Definition of fonts of the Tahoma font stack and its fallbacks"

    def __init__(self, builder: "LogBuilder"):
        """
        :param builder: The log builder
        """
        self.builder = builder

    def __call__(
        self,
        family: str | None = None,
        size: str | int | None = None,
        weight: float | None = None,
    ) -> ElementContext:
        """
        Returns a font context within which all text is written using this font and
        size

        :param family: The font's family
        :param size: The font's size. If no size is passed it will not be modified.
            If an integer is passed it will be handled as a pt value.
        :param weight: The fonts weight (from 0 to 1000)
        :return: The context
        """
        size_change: str = ""
        if size is not None:
            if isinstance(size, int):
                size = f"{size}pt"
            size_change = f";font-size: {size}"
        if weight is not None:
            size_change += f";font-weight: {weight}"
        family_change = ""
        if family is not None:
            family_change = f"font-family:{family}"
        html = f" <span style='{family_change};{size_change}'>"
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
        md_html = ""
        html = " <span class='vl_default_font'>"
        html_closing = "</span>"
        return ElementContext(
            builder=self.builder,
            opening_code={
                "html": html,
                "md": html if md_html else "",
            },
            closing_code={
                "html": html_closing,
                "md": html_closing if md_html else "",
            },
        )

    @property
    def arial(self) -> ElementContext:
        """Returns a new ElementContext selecting the Arial font stack"""
        return self(self._ARIAL_STACK)

    @property
    def trebuchet(self) -> ElementContext:
        """Returns a new ElementContext selecting the Trebuchet font stack"""
        return self(self._TREBUCHET)

    @property
    def times(self) -> ElementContext:
        """Returns a new ElementContext selecting the Times font stack"""
        return self(self._TIMES)

    @property
    def courier(self) -> ElementContext:
        """Returns a new ElementContext selecting the Courier New font stack"""
        return self(self._COURIER)

    @property
    def lucida(self) -> ElementContext:
        """Returns a new ElementContext selecting the Lucida font stack"""
        return self(self._LUCIDA)

    @property
    def georgia(self) -> ElementContext:
        """Returns a new ElementContext selecting the Georgia font stack"""
        return self(self._GEORGIA)

    @property
    def tahoma(self) -> ElementContext:
        """Returns a new ElementContext selecting the Tahoma font stack"""
        return self(self._TAHOMA)
