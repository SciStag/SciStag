"""
Defines the style config of an LSlider
"""

from __future__ import annotations

from typing import Union, Literal

from pydantic import BaseModel

from scistag.vislog.options.widget_options import LWidgetOptions


class LSliderOptions(LWidgetOptions):
    """
    Defines an LSlider's options
    """

    show_value: Union[bool, Literal["custom"]] = True
    """Defines if the value shall be shown next to the slider.
    
    If custom is assigned only the update logic will be logged and the user has to
    insert :attr:`LSlider.html_value_code` at the position at which he wants to
    visualize the current value"""
    vertical: bool = False
    """Defines if the slider shall be shown vertical"""
    value_prefix: str = ""
    """Text to be printed in front left of the value"""
    value_postfix: str = ""
    """Text to be printed right the value"""
    value_scaling: float = 1.0
    """Factor by which the value shall be scaled before being visualized"""
    value_max_digits: int = 0
    """The maximum count of digits the value shall visualize"""
    value_bold: bool = False
    """Defines if the value shall be displayed bold"""
    value_edit_field: bool = True
    """Defines if the value shall be shown as edit field"""
    vertical_width: str = "32pt"
    """The width in vertical mode"""
    vertical_height: str = "300pt"
    """The height in vertical mode"""
    horizontal_width: str = "300pt"
    """The width in horizontal mode"""
    horizontal_height: str = "32pt"
    """The height in horizontal mode"""

    def clone(self) -> LSliderOptions:
        """
        Creates a deep copy of the style

        :return: The style copy
        """
        return self.copy(deep=True)

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
