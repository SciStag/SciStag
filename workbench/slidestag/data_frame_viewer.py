from __future__ import annotations

import pandas as pd

from scistag.imagestag import Image
from scistag.imagestag.pandas_renderer import PandasRenderer
from scistag.slidestag import Widget, PaintEvent


class DataFrameViewer(Widget):
    # Additional parameters
    DATAFRAME = "df"
    "DataFrame parameter"
    HTML_OPTIONS = "htmlOptions"
    "HTML options"
    SHOW_INDEX = "showIndex"
    "Defines if the index shall be displayed"
    TABLE_WIDTH = "tableWidth"
    "The table's width. auto by default"
    AUTO_SIZE = "autoSize"
    "Defines if the view shall resize with the table"
    MAX_ROWS = "maxRows"
    "Defines the maximum number of rows to show. 20 by default"
    TABLE_STYLE = "tableStyle"
    "The table style"
    FONT_SIZE = "fontSize"
    "Font size"
    FONT_FAMILY = "fontFamily"
    "Font family"
    TEXT_ALIGN = "textAlign"
    "Text alignment"

    def __init__(self, parent: Widget | None, parameters: dict):
        """
        Initializer
        :param parent: The parent view
        :param parameters: The creation parameters. Adding>
        * df = The dataframe
        * tableWidth = The desired table width. auto by default.
        * htmlOptions = Advanced HTML options. See HtmlLogRenderer. No effect if HTML rendering is not used.
        * showIndex = Defines if the index shall be shown
        * tableStyle = The table style. See PandasRenderer
        * fontSize = The font size
        * fontFamily = The font family
        * textAlign = The text alignment. left by default.
        """
        super().__init__(parent, parameters)
        self._df: pd.DataFrame = parameters.get(self.DATAFRAME, None)
        if self._df is None:
            self._df = pd.DataFrame()
        self._table_width = parameters.get(self.TABLE_WIDTH, "auto")
        self._show_index: bool = parameters.get(self.SHOW_INDEX, False)
        self._table_style: str = parameters.get(self.TABLE_STYLE, "blue_light")
        self._font_size: str = parameters.get(self.FONT_SIZE, "20pt")
        self._auto_size: bool = parameters.get(self.AUTO_SIZE, True)
        self._max_rows: int = parameters.get(self.MAX_ROWS, 20)
        self._font_family: str = parameters.get(
            self.FONT_FAMILY, "Century Gothic, sans-serif"
        )
        self._text_align: str = parameters.get(self.TEXT_ALIGN, "left")
        self._html_options = parameters.get(self.HTML_OPTIONS, None)
        self.image: Image | None = None
        "The rendered image of the table"

    def set_df(self, df: pd.DataFrame) -> None:
        """
        Sets a new dataframe
        :param df: The new data
        """
        self._df = df

    def refresh(self):
        """
        Requests a repaint of the table. Call this function when the data frame's content was modified
        """
        self.temp_cache.remove("tableImage")
        self.repaint()

    def _update_image(self) -> Image:
        """
        Renders the new image of the table
        :return: The new image
        """
        df = self._df
        if self._max_rows != -1 and len(df) > self._max_rows:  # clip table if desired
            df = df.iloc[0 : self._max_rows]
        pandas_renderer = PandasRenderer(
            df=df,
            show_index=self._show_index,
            style=self._table_style,
            width=self._table_width,
            font_size=self._font_size,
            font_family=self._font_family,
            text_align=self._text_align,
        )
        result = pandas_renderer.render()
        if self._auto_size:
            if result.get_size() != self.size():
                self.set_size(result.get_size())
        return result

    def handle_paint(self, event: PaintEvent) -> bool:
        if not super().handle_paint(event):
            return False
        self.image = self.temp_cache.temp_cache("tableImage", None, self._update_image)
        event.canvas.draw_image(self.image, (0, 0))
        return True

    def handle_unload(self) -> bool:
        self.image = None
        return super().handle_unload()
