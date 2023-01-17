"""
Defines the configuration for tables
"""

from __future__ import annotations
from typing import Union, Literal

from pydantic import BaseModel


TABULATE_GITHUB = "github"
"Tabulate class for github markdown"

TABULATE_ROUNDED_OUTLINE = "rounded_outline"
"Tabulate class for rounded tables"

TABLE_CLASS_DATA = "vl_data_table"
"CSS class for data tables"

TABLE_CLASS_DEFAULT = "vl_log_table"
"CSS style for a basic table"

TABLE_CLASS_SEAMLESS = "vl_log_table_seamless"
"CSS style for a basic table without visible lines and padding"

DataTablesFormats = Literal[
    "txt", "vl_data_table", "vl_log_table", "github", "rounded_outline"
]
"""Definition if supported formats for data tables being logged e.g. via LogBuilder.np
or LogBuilder.pd"""


class TableOptions(BaseModel):
    """Defines the tables visual appearance"""

    seamless: bool = False
    """Defines if the table shall be visualized seamless, without padding and visible
    borders"""
    html_class: Union[str, None] = None
    """Explicit table class definition"""
    html_style: str = ""
    """Custom style"""
    data_table_format: dict[str, DataTablesFormats] = {
        "html": TABLE_CLASS_DATA,
        "md": TABULATE_GITHUB,
        "txt": TABULATE_ROUNDED_OUTLINE,
        "console": TABULATE_ROUNDED_OUTLINE,
    }
    """Defines the logging format of data tables."""

    def get_html_class(self):
        """
        Returns the effectice table class

        :return:
        """
        if self.html_class is not None:
            return self.html_class
        return TABLE_CLASS_SEAMLESS if self.seamless else TABLE_CLASS_DEFAULT

    def clone(self) -> TableOptions:
        """
        Returns a copy of this option set
        """
        copy = self.copy(deep=True)
        return copy
