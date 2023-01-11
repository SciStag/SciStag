from __future__ import annotations

from typing import TYPE_CHECKING

from scistag.imagestag import ImsFramework, Image

if TYPE_CHECKING:
    import pandas as pd


class PandasRenderer:
    """
    Helper class to convert a Pandas dataframe to an image
    """

    def __init__(
        self,
        df: "pd.DataFrame",
        show_index: bool = False,
        width: str | None = None,
        style="blue_light",
        font_size="medium",
        font_family="Century Gothic, sans-serif",
        text_align="left",
    ):
        """
        Initializer
        :param df: The dataframe
        :param show_index: Shall the index be shown?
        :param width: The base width. Automatic width by default
        :param style: The display style. See https://github.com/sbi-rviot/ph_table
        :param font_size: The font's size
        :param font_family: The font family
        :param text_align: The horizontal text alignment of. left, center, right
        """
        self.df = df
        from .html_renderer import HtmlRenderer

        self.html_renderer = HtmlRenderer()
        self.style = style
        self.show_index = show_index
        self.width = width if width is not None else "auto"
        self.font_size = font_size
        self.font_family = font_family
        self.text_align = text_align

    def render(self, html_options: dict | None = None) -> Image:
        """
        Renders the table to an image
        :param html_options: The advanced options for a HTML renderer. See HtmlLogRenderer. Optional.
        :return: The image
        """
        from scistag.vislog import VisualLog
        from scistag.vislog.builders.pandas_builder import (
            PandasBuilder,
            PandasBuilderParams,
        )

        options = VisualLog.setup_options()
        options.style.slim = True
        params = PandasBuilderParams(start=0, end=99)
        html = PandasBuilder.run(
            options=options, df=self.df, params=params, filetype="html"
        )

        options = html_options if html_options is not None else {}
        options["body"] = html
        if self.width != "auto" and "width" not in options:
            no_px = (
                self.width.rstrip("px") if isinstance(self.width, str) else self.width
            )
            if isinstance(no_px, int) or no_px.isnumeric():
                options["width"] = int(no_px)

        return self.html_renderer.render(options)
