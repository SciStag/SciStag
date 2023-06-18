"""
Tests VisualLog's testing capabilities for regression tests
"""
import os
import shutil
from unittest import mock

import numpy as np
import pandas as pd
import pytest

from . import vl
from ...filestag import FilePath, FileStag
from . import vl


def test_general_assertion():
    """
    Tests basic type assertion
    """
    with pytest.raises(NotImplementedError):
        vl.test.assert_val("abool", True)


def test_hash_replacement():
    """
    Tests the automatic replacement of hashes if a placeholder such as ??? is used as
    hash_id
    """

    test_dir = FilePath.dirname(__file__)
    ref_data_dir = test_dir + "/refdata/"
    base_path = test_dir + "/temp/"
    os.makedirs(base_path, exist_ok=True)

    cur_hash = "871c5bd6f3259422f3ea1f4b911ac2de"

    code = """
def dummy_test(vl):
    vl.test.checkpoint("shouldFail")
    vl.text("This should fail on purpose for a test")
    vl.test.assert_cp_diff("???", ref=False)
"""
    code_r = """
def dummy_test(vl):
    vl.test.checkpoint("shouldFail")
    vl.text("This should fail on purpose for a test")
    vl.test.assert_cp_diff("???")
"""
    code_second = """
def dummy_test2(vl):
    from scistag.vislog import VisualLog
    other = VisualLog().default_builder
    vl.test.checkpoint("shouldFail")
    vl.text("This should fail on purpose for a test")
    vl.test.assert_cp_diff("???", target=other, ref=True)
    """
    code_correct = f"""
def dummy_testc(vl):
    from scistag.vislog import VisualLog
    other = VisualLog().default_builder
    vl.test.checkpoint("shouldFail")
    vl.text("This should fail on purpose for a testx")
    vl.test.assert_cp_diff("{cur_hash}", target=other, ref=True)
    """
    code_third = """
def dummy_test3(vl):
    from scistag.vislog import VisualLog
    other = VisualLog().default_builder
    vl.test.checkpoint("shouldFail")
    vl.text("This should fail on purpose for a test")
    vl.test.assert_cp_diff("123456", target=other, ref=True)
        """
    FileStag.save_text(base_path + "./__init__.py", "")
    FileStag.save_text(base_path + "./generic_hash_replace_nr.py", code)
    FileStag.save_text(base_path + "./generic_hash_replace.py", code_r)
    FileStag.save_text(base_path + "./generic_hash_replace_2.py", code_second)
    FileStag.save_text(base_path + "./generic_hash_replace_c.py", code_correct)
    FileStag.save_text(base_path + "./generic_hash_replace_3.py", code_third)
    from .temp.generic_hash_replace_nr import dummy_test

    dummy_test(vl)

    from .temp.generic_hash_replace import dummy_test

    dummy_test(vl)
    from .temp.generic_hash_replace_2 import dummy_test2

    try:
        os.remove(ref_data_dir + f"/{cur_hash}.html")
    except FileNotFoundError:
        pass

    dummy_test2(vl)

    from .temp.generic_hash_replace_c import dummy_testc

    with pytest.raises(AssertionError):
        dummy_testc(vl)

    from .temp.generic_hash_replace_3 import dummy_test3

    with pytest.raises(AssertionError):
        dummy_test3(vl)
    rl_text = FileStag.load_text(base_path + "./generic_hash_replace.py")
    assert len(rl_text) and "???" not in rl_text


def test_hash_replacement_df():
    """
    Tests the automatic replacement of hashes for data frames
    """
    d = {
        "one": pd.Series([10, 20, 30, 40], index=["a", "b", "c", "d"]),
        "two": pd.Series([10, 20, 30, 40], index=["a", "b", "c", "d"]),
    }
    df = pd.DataFrame(d)
    test_dir = FilePath.dirname(__file__)
    ref_data_dir = test_dir + "/refdata/"
    base_path = test_dir + "/temp/"
    os.makedirs(base_path, exist_ok=True)

    code = """
def dummy_test_df(vl, df):
    vl.test.assert_df("testdf", df, hash_val="123")
"""
    FileStag.save_text(base_path + "./__init__.py", "")
    FileStag.save_text(base_path + "./generic_df_hash_replace.py", code)
    from .temp.generic_df_hash_replace import dummy_test_df

    dummy_test_df(vl, df)
