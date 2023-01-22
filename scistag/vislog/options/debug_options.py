"""
Defines debugging specific options
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from scistag.vislog.options.html_client_options import HtmlClientDebugOptions


class LogDebugOptions(BaseModel):
    """
    Debug options
    """

    html_client: HtmlClientDebugOptions = Field(default_factory=HtmlClientDebugOptions)

    def enable(self):
        """
        Enabled a standard debugging options set
        """
        self.html_client.log_updates = True

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
