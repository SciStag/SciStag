"""
Definition of Markdown (.md) specific logging options
"""

from __future__ import annotations

from pydantic import BaseModel


class MdOptions(BaseModel):
    """
    Defines Markdown specific configuration options
    """

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
