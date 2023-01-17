from __future__ import annotations

from pydantic import BaseModel


class PageOptions(BaseModel):
    """
    Option set for general page properties
    """

    title: str = "SciStag - VisualLog"
    """The page's initial title"""

    def setup(self, title: str | None = None):
        """
        Setups the page options

        :param title: The page's title
        """
        if title is not None:
            self.title = title

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
