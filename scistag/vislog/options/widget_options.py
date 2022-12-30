"""
Defines the class LWidgetOptions which is the shared base class for widget
configurations
"""

from pydantic import BaseModel


class LWidgetOptions(BaseModel):
    """
    Defines a widget's options such as its appearance
    """
