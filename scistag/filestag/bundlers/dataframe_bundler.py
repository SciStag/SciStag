"""
Bundles and unpacks Pandas DataFrames, see :class:`Bundle`
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import io

from scistag.filestag.bundle import BundlingOptions, UnpackOptions

if TYPE_CHECKING:
    import pandas as pd


class DataFrameBundler:
    """
    Bundles and unpacks Pandas data, see :class:`Bundle`
    """

    DF_CLASS_NAME = 'pandas.core.frame.DataFrame'
    "Full qualified name of DataFrame class"

    @classmethod
    def bundle(cls, data: "pd.DataFrame",
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
        return cls.DF_CLASS_NAME, stream.getvalue()

    @staticmethod
    def unpack(data: bytes, options: UnpackOptions | None = None) -> \
            "pd.DataFrame":
        """
        Restores a Pandas DataFrame from bytes

        :param data: The data to be unpacked
        :param options: The unpacking options
        :return: The restored numpy array
        """
        from scistag.optional.pyarrow_opt import ensure_pyarrow
        import pandas as pd
        ensure_pyarrow()
        comp_df = pd.read_parquet(io.BytesIO(data), engine='pyarrow')
        return comp_df


class DataSeriesBundler:
    """
    Bundles and unpacks Pandas series, see :class:`Bundle`
    """

    SERIES_CLASS_NAME = 'pandas.core.series.Series'
    "Full qualified name of Series class"

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
        return cls.SERIES_CLASS_NAME, stream.getvalue()

    @staticmethod
    def unpack(data: bytes, options: UnpackOptions | None = None) -> \
            "pd.Series":
        """
        Restores a Pandas DataFrame from bytes

        :param data: The data to be unpacked
        :param options: The unpacking options
        :return: The restored numpy array
        """
        from scistag.optional.pyarrow_opt import ensure_pyarrow
        ensure_pyarrow()
        import pandas as pd
        series = pd.read_pickle(io.BytesIO(data))
        return series
