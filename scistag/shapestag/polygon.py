"""
Implements :class:`Polygon` define polygonal shapes

Not implemented yet.
"""
from __future__ import annotations
import typing
from abc import abstractmethod

from scistag.imagestag import Pos2D
from scistag.shapestag import Shape

if typing.TYPE_CHECKING:
    import numpy as np


class Polygon(Shape):
    """
    Defines a polygonal shape
    """

    @abstractmethod
    def __init__(self):
        super().__init__("Polygon", set())
        raise NotImplementedError("Polygons are not supported yet")

    @staticmethod
    def get_bounding_from_points(points: "np.ndarray") -> \
            tuple[Pos2D, Pos2D] | None:
        """
        Computes the bounding from a set of points

        :param points: The polygon's points
        :return: Upper left (smaller x and y), lower right edge (greater x
            and y). None if the list if None or empty
        """
        import numpy as np
        if points is None or points.shape[0] == 0 or len(points.shape) != 2:
            return None
        top_left = np.array(points).min(axis=0)
        bottom_right = np.array(points).max(axis=0)
        return Pos2D(top_left[0], top_left[1]), Pos2D(bottom_right[0],
                                                      bottom_right[1])
