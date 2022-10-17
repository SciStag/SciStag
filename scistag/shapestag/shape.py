"""
Implements the :class:`Shape: class, the base element for all dynamic Shapes
which can be rendered into a canvas.
"""
from __future__ import annotations
import hashlib
import typing
from abc import abstractmethod
from dataclasses import dataclass

from scistag.imagestag import Canvas, Colors, Bounding2D, Image


@dataclass
class Shape:
    """
    Defines a shape which can be rendered
    """

    shape_class: str = ""
    "The shape's class"

    bounding: Bounding2D = Bounding2D((0.0, 0.0, 0.0, 0.0))
    "The region to be covered overall"

    HASHABLE_PROPERTIES: typing.ClassVar = {"shape_class"}

    def __init__(self, class_name: str, hashable_properties: set[str]):
        """
        Initializer

        :param class_name: The class name
        :param hashable_properties: The properties which can automatically
            get hashed by value to string conversion.
        """
        super().__init__()
        self.shape_class = class_name
        "The shape's class"
        self.__dict__["_hashable_properties"] = hashable_properties
        "The properties which can be used to create a unique hash"

    @abstractmethod
    def draw(self, target: Canvas, options: dict | None = None):
        """
        Draws the shape into the defined canvas

        :param target: The canvas to render onto
        :param options: Advanced options, such as the cache in which the shape
            might be cached.
        """
        pass

    def to_image(self, background_color=Colors.TRANSPARENT) -> Image:
        """
        Renders the shape to an image.

        The shape needs to either specify it's bounding or it's size as
        member variable to be convertible.

        :param background_color: The background color
        """
        bounding: Bounding2D = self.bounding
        offset = bounding.pos.to_tuple()
        # to see the whole object and as it is painted relative
        # we need to invert the offset, e.g. an object starting at
        # -50, -50 has to start painting relative 50, 50 so -50, -50
        # is still in the image (in this case at 0,0)
        offset = (-offset[0], -offset[1])
        size = bounding.get_size_tuple()
        tar = Canvas(size=size,
                     default_color=background_color)
        if offset != (0.0, 0.0):
            tar.add_offset_shift(offset)
        self.draw(tar)
        return tar.to_image()

    def get_hash(self) -> str:
        """
        A unique hash of the data in this shape. Is used to cache the
        shape's renderings when it has not been modified.

        :return: The hash value
        """
        data = []
        for element in self.__dict__["hashable_properties"]:
            element_data = self.__dict__[element]
            if isinstance(element, list):
                for index, data in enumerate(element_data):
                    data.append(f"@{element}.{index}")
                    data.append(str(data))
            else:
                data.append(f"@{element}")
                data.append(str(element_data))
        return hashlib.md5(bytearray(";".join(data), "utf-8")).hexdigest()
