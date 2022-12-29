"""
Defines the configuration options for VisualLog and associated classes
"""

from pydantic import BaseModel, Field

from scistag.vislog.options import LSliderOptions


class HtmlClientDebugOptions(BaseModel):
    """
    Html client debug options
    """

    log_updates: bool = False
    """Defines if modifications to the dom structure shall be logged"""


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


class LogStyles(BaseModel):
    """
    Defines the default style for all elements
    """

    slider: LSliderOptions = Field(default_factory=LSliderOptions)


class LogOptions(BaseModel):
    """
    Defines the configuration of a VisualLog
    """

    style: LogStyles = Field(default_factory=LogStyles)
    debug: LogDebugOptions = Field(default_factory=LogDebugOptions)
