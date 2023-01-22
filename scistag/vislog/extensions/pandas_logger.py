"""
Implements the :class:`PandasLogger` extension for LogBuilder to log
Pandas DataFrames, DataSeries and statistics about them to a log.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from scistag.vislog import BuilderExtension, LogBuilder, HTML, MD, TXT, CONSOLE
from scistag.vislog.builders.pandas_builder import PandasBuilder, PandasBuilderParams
from scistag.vislog.options.table_options import (
    TABULATE_ROUNDED_OUTLINE,
    TABULATE_GITHUB,
)

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
        to = self.builder.options.style.table
        formats = self.builder.options.output.formats_out

        def get_table_in_format(cur_format: str):
            if cur_format.startswith("vl_"):
                params = PandasBuilderParams(start=0, end=99)
                html_code = self.builder.builder.run(
                    PandasBuilder,
                    params=params,
                    df=df,
                ).output["index.html"]
                return html_code.decode("utf-8")
            if cur_format == TABULATE_ROUNDED_OUTLINE or cur_format == TABULATE_GITHUB:
                return df.to_markdown(index=index, tablefmt=cur_format)
            return df.to_string(index=index)

        if HTML in formats:
            tf = to.data_table_format[HTML]
            code = get_table_in_format(tf)
            if not tf.startswith("vl_"):
                code = "<pre class='logtext'>\n" + code + "\n</pre>\n"
            self.builder.add_html(code)
        if MD in formats:
            tf = to.data_table_format[MD]
            code = get_table_in_format(to.data_table_format[MD])
            if tf != HTML and tf != TABULATE_GITHUB:
                code = "```\n" + code + "\n```\n"
            else:
                code = code + "\n"
            self.builder.add_md(code)
        if TXT or CONSOLE in formats:
            self.builder.add_txt(get_table_in_format(to.data_table_format[TXT]))
        self.page_session.handle_modified()
