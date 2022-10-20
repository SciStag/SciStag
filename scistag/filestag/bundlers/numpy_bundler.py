"""
Bundles and unpacks numpy data, see :class:`Bundle`
"""

from __future__ import annotations

import io

import numpy as np

from scistag.filestag.bundle import BundlingOptions, UnpackOptions


class NumpyBundler:
    """
    Bundles and unpacks numpy data, see :class:`Bundle`
    """

    @classmethod
    def bundle(cls, data: np.ndarray, options: BundlingOptions | None = None) -> (
            str, bytes):
        """
        Bundled a numpy array to a bytes stream

        :param data: The data to be packed
        :param options: The bundling options
        :return: The packed data as single bytes strings
        """
        stream = io.BytesIO()
        np.save(stream, data)
        return cls.__name__, stream.getvalue()

    @staticmethod
    def unpack(data: bytes, options: UnpackOptions | None = None) -> np.ndarray:
        """
        Unpacks the data

        :param data: The data to be unpacked
        :param options: The unpacking options
        :return: The restored numpy array
        """
        return np.load(io.BytesIO(data))
