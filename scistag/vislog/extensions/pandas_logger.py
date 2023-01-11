"""
Implements the :class:`PandasLogger` extension for LogBuilder to log
Pandas DataFrames, DataSeries and statistics about them to a log.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from scistag.vislog import BuilderExtension, LogBuilder
from scistag.vislog.builders.pandas_builder import PandasBuilder, PandasBuilderParams

if TYPE_CHECKING:
    import pandas as pd


class PandasLogger(BuilderExtension):
    """
    The Pandas logger adds the feature to log Pandas DataFrames, DataSeries
    and statistics about data to the log.
    """

    def __init__(self, builder: LogBuilder):
        """
        :param builder: The builder we are using to write to the log
        """
        super().__init__(builder)
        self.show = self.__call__
        self.use_tabulate = True
        "Defines if tabulate may be used"
        self.use_pretty_html_table = True
        "Defines if pretty html shall be used"
        self.html_table_style = "blue_light"
        "The pretty html style to be used"
        self.txt_table_format = "rounded_outline"
        "The text table format to use in tabulate"
        self.md_table_format = "github"
        "The markdown table format to use"

    def __call__(
        self,
        df: "pd.DataFrame",
        name: str | None = None,
        index: bool = True,
        max_rows: int = 100,
    ):
        """
        Logs a dataframe to the log

        :param name: The dataframe's name
        :param df: The data frame
        :param index: Defines if the index shall be printed
        :param max_rows: The maximum number of rows to log
        """
        if df.shape[0] > max_rows:
            df = df.head(max_rows)
        if name is None:
            name = "dataframe"
        if self.use_pretty_html_table:
            params = PandasBuilderParams(start=0, end=99)
            html_code = self.builder.builder.run(
                PandasBuilder, params=params, df=df
            ).output["index.html"]
        else:
            html_code = df.to_html(index=index)
        self.builder.add_html(html_code)
        if self.use_tabulate:
            md_table = df.to_markdown(index=index, tablefmt=self.md_table_format)
            self.builder.add_md(md_table)
            self.builder.add_txt(
                df.to_markdown(index=index, tablefmt=self.txt_table_format) + "\n"
            )
        else:
            string_table = df.to_string(index=index) + "\n"
            if self.target_log.markdown_html:
                self.builder.add_md(html_code)
            else:
                self.builder.add_md(string_table)
            self.builder.add_txt(string_table)
        self.page_session.handle_modified()
