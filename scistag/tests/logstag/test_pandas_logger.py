"""
Tests the pandas specific logging functions
"""

import shutil
from unittest import mock

import numpy as np
import pytest

from . import vl


def test_dataframe():
    """
    Tests dataframe logging
    """
    vl.test.begin("Pandas DataFrame logging")
    # logging data frames
    import pandas as pd
    d = {'one': pd.Series([10, 20, 30, 40],
                          index=['a', 'b', 'c', 'd']),
         'two': pd.Series([10, 20, 30, 40],
                          index=['a', 'b', 'c', 'd'])}
    df = pd.DataFrame(d)
    vl.test.checkpoint()
    vl.sub_test("Logging a simple Pandas DataFrame")
    vl.df(df, "A simple dataframe")
    vl.test.checkpoint()
    vl.test.assert_cp_diff(hash_val="d41d8cd98f00b204e9800998ecf8427e")
    vl.sub_test("HTML table printed w/o pretty html")
    vl.target_log.use_pretty_html_table = False
    vl.df(df, "A simple dataframe w/o pretty html")
    vl.target_log.use_pretty_html_table = True
    vl.test.assert_cp_diff(hash_val="cdc3b666bc3d8a22556fd9b9bbd713f9")

    # testing data frame assertion
    with mock.patch('builtins.print'):
        vl.test.assert_df("test_dataframe", df, dump=True)
    vl.test.assert_df("test_dataframe", df)
    with pytest.raises(AssertionError):
        vl.test.assert_df("test_dataframe_no_data", df)
    vl.test.assert_val("test_dataframe", df)
    vl.test.assert_df("test_dataframe", df,
                      hash_val="914de108cea30eb542f1fb57dcb18afc")
    with pytest.raises(AssertionError):
        df.loc['a', 'one'] = 'NewValue'
        vl.test.assert_df("test_dataframe", df)
    with pytest.raises(AssertionError):
        vl.test.assert_df("test_dataframe", df,
                          hash_val="914de108cea30eb542f1fb57dcb18afc")
    vl.sub_test("Log table without tabulate")
    vl.target_log.use_tabulate = False
    vl.df(df, "DataFrame w/o tabulate")
    vl.sub_test("Log table without HTML")
    vl.markdown_html = False
    vl.df(df, "DataFrame w/o tabulate")
    vl.markdown_html = True
    vl.target_log.use_tabulate = True
    vl.df(df, "DataFrame w/o tabulate")
    vl.target_log.use_tabulate = True
