"""
Defines the :class:`ShapeList` class
"""
from typing import DefaultDict

from scistag.imagestag import Canvas
from scistag.shapestag import Shape


class ShapeList(Shape):
    """
    A collection of shapes
    """

    def __init__(self):
        super().__init__()

    def draw(self, target: Canvas, options: dict = None):
        pass
