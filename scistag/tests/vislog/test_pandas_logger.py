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
    vl.test.checkpoint("log.df.simple")
    vl.sub_test("Logging a simple Pandas DataFrame")
    vl.pd(df, "A simple dataframe")
    vl.test.checkpoint("log.table.pretty")
    vl.test.assert_cp_diff(hash_val="d41d8cd98f00b204e9800998ecf8427e")
    vl.sub_test("HTML table printed w/o pretty html")
    vl.pd.use_pretty_html_table = False
    vl.pd(df, "A simple dataframe w/o pretty html")
    vl.pd.use_pretty_html_table = True
    vl.test.assert_cp_diff(hash_val="5b7ebe8357ae21f9eade9f47f019b2c7")

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
    vl.pd.use_tabulate = False
    vl.pd(df, "DataFrame w/o tabulate")
    vl.sub_test("Log table without HTML")
    vl.target_log.markdown_html = False
    vl.pd(df, "DataFrame w/o tabulate")
    vl.target_log.markdown_html = True
    vl.pd.use_tabulate = True
    vl.pd(df, "DataFrame w/o tabulate")
    vl.pd.use_tabulate = True

    vl.test.checkpoint("pd.df.wohtml")
    md_state = vl.target_log.markdown_html
    use_tab = vl.pd.use_tabulate
    vl.pd.use_tabulate = False
    vl.target_log.markdown_html = False
    vl.pd(df, "DataFrame w/o html")
    vl.target_log.markdown_html = md_state
    vl.pd.use_tabulate = use_tab
    vl.test.assert_cp_diff('325f8fec160d80bf3769b6832731a738')

    vl.test.checkpoint("pd.df.nameless")
    vl.pd(df, name=None)
    vl.test.assert_cp_diff('625d2b1958c13dd6ec8303b4dcb70eb2')

    vl.test.checkpoint("pd.df.add")
    vl.add(df)
    vl.test.assert_cp_diff('625d2b1958c13dd6ec8303b4dcb70eb2')
