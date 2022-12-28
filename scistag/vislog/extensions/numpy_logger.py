"""
Implements the :class:`NumpyLogger` extension for VisualLogBuilder to log
numpy data such as matrices and vectors.
"""
from __future__ import annotations

import typing

from scistag.vislog import BuilderExtension, VisualLogBuilder

if typing.TYPE_CHECKING:
    import numpy as np

MAX_NP_ARRAY_SIZE = 100
"""
The maximum size the numpy arrays is allowed to have
"""


class NumpyLogger(BuilderExtension):
    """
    The Numpy logger adds the feature to log content of numpy arrays in various
    ways.
    """

    def __init__(self, builder: VisualLogBuilder):
        """
        :param builder: The builder we are using to write to the log
        """
        super().__init__(builder)
        self.show = self.__call__

    def __call__(self, data: "np.ndarray", max_digits=2, br: bool = True):
        """
        Adds a numpy matrix or vector to the log

        :param data: The data frame
        :param max_digits: The number of digits with which the numbers shall be
            formatted.
        :param br: Defines if the table shall be followed by a line break
        """
        if len(data.shape) >= 3:
            raise ValueError("Too many dimensions")
        if len(data.shape) == 1:
            data = [[f"{round(element, max_digits)}" for element in data]]
        else:
            if data.shape[0] > MAX_NP_ARRAY_SIZE or data.shape[1] > MAX_NP_ARRAY_SIZE:
                raise ValueError("Data too large")
            data = [
                [f"{round(element, max_digits)}" for element in row] for row in data
            ]
        self.builder.table(data, br=br)
