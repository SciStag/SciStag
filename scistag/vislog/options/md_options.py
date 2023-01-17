from __future__ import annotations

from pydantic import BaseModel


class MdOptions(BaseModel):
    """
    Defines Markdown specific configuration options
    """

    support_html: bool = True
    """Defines if using HTML is supported"""

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
