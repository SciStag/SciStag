from enum import Enum

from .event import WidgetEvent, WidgetEventHandler
from scistag.imagestag.canvas import Canvas


class PaintEvent(WidgetEvent):
    """
    The paint event. Is triggered when ever the view is repainted
    """

    def __init__(self, widget, canvas: Canvas, config: dict):
        """
        Initializer
        :parma widget: The widget
        :param canvas: The target canvas
        :param config: The rendering config
        """
        super().__init__(widget=widget)
        self.canvas = canvas
        self.config = config


class TouchEvent(WidgetEvent):
    """
    Shared base class for all touch and click based events
    """

    def __init__(self, widget):
        super().__init__(widget)


class MouseButton(Enum):
    """
    Enumeration of mouse buttons for Touch- and Drag events
    """
    LEFT = 0
    "Left mouse button or the finger"
    MIDDLE = 1
    "Center mouse button"
    RIGHT = 2
    "Right mouse button"


class TapEvent(TouchEvent):
    """
    Defines an event which is raised when the mouse button is clicked or a finger hits the screen
    """

    def __init__(self, widget, coordinate, coordinate_absolute,
                 button: MouseButton):
        """
        Initializer
        :param widget: The widget
        :param coordinate: The precise, relative coordinate
        :param coordinate_absolute: The absolute coordinate (relative to the main window)
        :param button: The mouse button pressed (left/mid/right)
        """
        super().__init__(widget)
        self.coordinate = coordinate
        self.coordinate_absolute = coordinate_absolute
        self.button: MouseButton = button


__all__ = ["WidgetEventHandler", "WidgetEvent", "PaintEvent", "TapEvent",
           "MouseButton"]
