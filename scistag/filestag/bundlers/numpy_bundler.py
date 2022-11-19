"""
Bundles and unpacks numpy data, see :class:`Bundle`
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import io

from scistag.filestag.bundle import BundlingOptions, UnpackOptions

if TYPE_CHECKING:
    import numpy as np


class NumpyBundler:
    """
    Bundles and unpacks numpy data, see :class:`Bundle`
    """

    NP_CLASS_NAME = 'numpy.ndarray'

    @classmethod
    def bundle(cls, data: "np.ndarray",
               options: BundlingOptions | None = None) -> (
            str, bytes):
        """
        Bundled a numpy array to a bytes stream

        :param data: The data to be packed
        :param options: The bundling options
        :return: The packed data as single bytes strings
        """
        stream = io.BytesIO()
        import numpy as np
        np.save(stream, data)
        return cls.NP_CLASS_NAME, stream.getvalue()

    @staticmethod
    def unpack(data: bytes, options: UnpackOptions | None = None) -> np.ndarray:
        """
        Unpacks the data

        :param data: The data to be unpacked
        :param options: The unpacking options
        :return: The restored numpy array
        """
        import numpy as np
        return np.load(io.BytesIO(data))
