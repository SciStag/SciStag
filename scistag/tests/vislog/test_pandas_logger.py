"""
Tests the pandas specific logging functions
"""

import shutil
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock

import pandas as pd
import pytest

from . import vl
from ...vislog.options.table_options import TABULATE_ROUNDED_OUTLINE, TABLE_CLASS_DATA

d = {
    "one": pd.Series([10, 20, 30, 40], index=["a", "b", "c", "d"]),
    "two": pd.Series([10, 20, 30, 40], index=["a", "b", "c", "d"]),
}
df = pd.DataFrame(d)


def test_dataframe():
    """
    Tests dataframe logging
    """
    vl.test.begin("Pandas DataFrame logging")
    # logging data frames

    vl.test.checkpoint("log.df.simple")
    vl.sub_test("Logging a simple Pandas DataFrame")
    vl.pd(df, "A simple dataframe")
    vl.test.checkpoint("log.table.pretty")
    vl.test.assert_cp_diff(hash_val="d41d8cd98f00b204e9800998ecf8427e")
    prev = vl.options.style.table.data_table_format["html"]
    vl.options.style.table.data_table_format["html"] = TABULATE_ROUNDED_OUTLINE
    vl.sub_test("HTML table printed as text")
    vl.pd(df, "A simple dataframe w/o pretty html")
    vl.test.assert_cp_diff(hash_val="605f8c2ed24564719d15182347804231")
    vl.options.style.table.data_table_format["html"] = prev

    std_out = StringIO()
    with redirect_stdout(std_out):
        # testing data frame assertion
        with mock.patch("builtins.print"):
            vl.test.assert_df("test_dataframe", df, dump=True)
    vl.test.assert_df("test_dataframe", df)
    with pytest.raises(AssertionError):
        vl.test.assert_df("test_dataframe_no_data", df)
    vl.test.assert_val("test_dataframe", df)
    vl.test.assert_df("test_dataframe", df, hash_val="914de108cea30eb542f1fb57dcb18afc")
    with pytest.raises(AssertionError):
        df.loc["a", "one"] = "NewValue"
        vl.test.assert_df("test_dataframe", df)
    with pytest.raises(AssertionError):
        vl.test.assert_df("test_dataframe", df, hash_val="locked719f4e4e220e146a50422ba1b60a1ba6")

    vl.test.checkpoint("pd.df.wohtml")
    vl.pd(df, "DataFrame w/o html")


def test_add():
    vl.test.checkpoint("pd.df.nameless")
    vl.pd(df, name=None)
    vl.test.assert_cp_diff("ec571505698e024c483e97277bcb9c12")

    vl.test.checkpoint("pd.df.add")
    vl.add(df, br=True)
    vl.test.assert_cp_diff("ec571505698e024c483e97277bcb9c12")

    vl.test.checkpoint("pd.df.row_limit")
    # log with limited count of rows
    vl.pd(df, max_rows=2)
    vl.test.assert_cp_diff("2a43c33a541edd425dff1ede13ebf31b")
