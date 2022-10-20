"""
Bundles and unpacks Pandas DataFrames, see :class:`Bundle`
"""

from __future__ import annotations

import io

import pandas as pd

from scistag.filestag.bundle import BundlingOptions, UnpackOptions


class DataFrameBundler:
    """
    Bundles and unpacks Pandas data, see :class:`Bundle`
    """

    @classmethod
    def bundle(cls, data: pd.DataFrame,
               options: BundlingOptions | None = None) -> (
            str, bytes):
        """
        Bundles a Pandas DataFrame to bytes

        :param data: The data to be packed
        :param options: The bundling options
        :return: The packed data as single bytes strings
        """
        from scistag.optional.pyarrow_opt import ensure_pyarrow
        ensure_pyarrow()
        stream = io.BytesIO()
        data.to_parquet(stream, engine='pyarrow')
        return cls.__name__, stream.getvalue()

    @staticmethod
    def unpack(data: bytes, options: UnpackOptions | None = None) -> \
            pd.DataFrame:
        """
        Restores a Pandas DataFrame from bytes

        :param data: The data to be unpacked
        :param options: The unpacking options
        :return: The restored numpy array
        """
        from scistag.optional.pyarrow_opt import ensure_pyarrow
        ensure_pyarrow()
        comp_df = pd.read_parquet(io.BytesIO(data), engine='pyarrow')
        return comp_df


class DataSeriesBundler:
    """
    Bundles and unpacks Pandas series, see :class:`Bundle`
    """

    @classmethod
    def bundle(cls, data: pd.Series,
               options: BundlingOptions | None = None) -> (
            str, bytes):
        """
        Bundles a Pandas DataFrame to bytes

        :param data: The data to be packed
        :param options: The bundling options
        :return: The packed data as single bytes strings
        """
        from scistag.optional.pyarrow_opt import ensure_pyarrow
        ensure_pyarrow()
        stream = io.BytesIO()
        data.to_pickle(stream)
        return cls.__name__, stream.getvalue()

    @staticmethod
    def unpack(data: bytes, options: UnpackOptions | None = None) -> \
            pd.Series:
        """
        Restores a Pandas DataFrame from bytes

        :param data: The data to be unpacked
        :param options: The unpacking options
        :return: The restored numpy array
        """
        from scistag.optional.pyarrow_opt import ensure_pyarrow
        ensure_pyarrow()
        series = pd.read_pickle(io.BytesIO(data))
        return series
