"""
Defines the log's style options :class:`LogStyleOptions`
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from scistag.vislog.options.slider_options import LSliderOptions
from scistag.vislog.options.table_options import TableOptions
from scistag.vislog.options.image_options import ImageOptions


class LogStyleOptions(BaseModel):
    """
    Defines the default style for all elements
    """

    slider: LSliderOptions = Field(default_factory=LSliderOptions)
    """Default options for a slider"""
    table: TableOptions = Field(default_factory=TableOptions)
    """Default options for a table"""
    image: ImageOptions = Field(default_factory=ImageOptions)
    """Image options"""
    slim: bool = False
    """Defines if optional components such footers and footers shall be removed"""

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
