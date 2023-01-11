"""
Implements :class:`PandasBuilder` which renders a pandas dataframe as table
"""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, validator

from scistag.vislog import LogBuilder, cell


class PandasBuilderParams(BaseModel):
    """
    Defines the Pandas builder parameters
    """

    start: int = 0
    """The first row to show"""
    end: int = 99
    """The last row to show"""


class PandasBuilder(LogBuilder):
    """
    Renders a Pandas DataFrame as HTML table

    Supported (dynamic) parameters:
    * start: The first row to show
    * end: The last row to show (inclusive). By default start+99
    """

    param_class = PandasBuilderParams

    def __init__(
        self, df: pd.DataFrame, params: PandasBuilderParams | dict | None, **kwargs
    ):
        """
        :param df: The data frame which holds the data
        :param params: The build parameters, e.g. the row range
        :param kwargs:
        """
        super().__init__(params=params, **kwargs)
        self.data_frame: pd.DataFrame = df
        self.params: PandasBuilderParams = self.params

    @cell(static=True)
    def build_table(self):
        """
        Renders the dataframe as a HTML table
        """
        df = self.data_frame
        start = self.params.start
        end = self.params.end
        if end >= len(df.index):
            end = len(df.index) - 1
        if start < 0 or start >= len(df.index) or end < start:
            df = None
        if df is None:
            return
        df = df.iloc[start : end + 1]
        with self.table.begin(
            header=True, index=True, html_class="vl_data_table"
        ) as table:
            table.add_row([""] + df.keys().tolist())
            for row_index, index in enumerate(df.index):
                row_data = df.iloc[row_index]
                index_name = df.index[row_index]
                content: list = row_data.to_numpy().tolist()
                content.insert(0, index_name)
                table.add_row(content)
