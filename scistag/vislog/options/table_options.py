"""
Defines the configuration for tables
"""

from __future__ import annotations
from typing import Union

from pydantic import BaseModel

_TABLE_CLASS_DEFAULT = "vl_log_table"
"CSS style for a basic table"

_TABLE_CLASS_SEAMLESS = "vl_log_table_seamless"
"CSS style for a basic table without visible lines and padding"


class LogTableOptions(BaseModel):
    """Defines the tables visual appearance"""

    seamless: bool = False
    """Defines if the table shall be visualized seamless, without padding and visible
    borders"""
    html_class: Union[str, None] = None
    """Explicit table class definition"""
    html_style: str = ""
    """Custom style"""

    def get_html_class(self):
        """
        Returns the effectice table class

        :return:
        """
        if self.html_class is not None:
            return self.html_class
        return _TABLE_CLASS_SEAMLESS if self.seamless else _TABLE_CLASS_DEFAULT

    def clone(self) -> LogTableOptions:
        """
        Returns a copy of this option set
        """
        copy = self.copy(deep=True)
        return copy
