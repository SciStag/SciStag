"""
Container for format specific options
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from scistag.vislog.options.md_options import MdOptions


class FormatOptions(BaseModel):
    """
    Contains format specific options for each file type
    """

    md: MdOptions = Field(default_factory=MdOptions)
    """Markdown specific options"""

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
        self.md.validate_options()
