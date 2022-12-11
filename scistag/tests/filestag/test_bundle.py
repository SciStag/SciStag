"""
Tests the Bundle class which can store arbitrary data in a byte stream and
restore it from there - similar to pickling but with easier ways for
customization and limitation.
"""
import numpy as np
import pandas as pd

from scistag.filestag import Bundle


def test_bundle_basics():
    """
    Tests the bundling and unbundling basics
    """
    # dict
    simple_data = {
        "aString": "Text",
        "anInt": 1234,
        "aFloat": 1.234,
        "aBool": True,
        "aList": [1234],
        "aDict": {"a": "x", "b": "y"},
    }
    stored = Bundle.bundle(simple_data)
    restored_dict = Bundle.unpack(stored)
    assert simple_data == restored_dict
    # list
    simple_list = [True, [123], "Test", {"a": "x", "b": "y"}]
    stored = Bundle.bundle(simple_list)
    restored_list = Bundle.unpack(stored)
    assert isinstance(restored_list, list)
    assert simple_list == restored_list
    simple_tuple = ((53, 68), True, [123], "Test", {"a": "x", "b": "y"})
    stored = Bundle.bundle(simple_tuple)
    restored_tuple = Bundle.unpack(stored)
    assert isinstance(restored_tuple, tuple)
    assert simple_tuple == restored_tuple


def test_bundle_numpy():
    """
    Tests the bundling of NumPy data
    """
    # dict with float matrix
    simple_data = {
        "aString": "Text",
        "anInt": 1234,
        "aFloat": 1.234,
        "ones": np.ones((32, 32), dtype=float),
    }
    stored = Bundle.bundle(simple_data)
    restored_dict = Bundle.unpack(stored)
    assert np.all(simple_data["ones"] == restored_dict["ones"])
    del simple_data["ones"]
    del restored_dict["ones"]
    assert simple_data == restored_dict
    # dict with int matrix
    simple_data = {
        "aString": "Text",
        "anInt": 1234,
        "aFloat": 1.234,
        "ones": np.ones((32, 32), dtype=int),
    }
    stored = Bundle.bundle(simple_data)
    restored_dict = Bundle.unpack(stored)
    assert np.all(simple_data["ones"] == restored_dict["ones"])


def test_pandas():
    """
    Tests the bundling of Pandas DataFrames
    """
    d = {
        "one": pd.Series([10, 20, 30, 40], index=["a", "b", "c", "d"]),
        "two": pd.Series([10, 20, 30, 40], index=["a", "b", "c", "d"]),
    }
    df = pd.DataFrame(d)
    # dict with pandas dataframe
    simple_data = {"aString": "Text", "anInt": 1234, "aFloat": 1.234, "dataFrame": df}
    stored = Bundle.bundle(simple_data)
    restored_dict = Bundle.unpack(stored)
    assert np.all(simple_data["dataFrame"] == restored_dict["dataFrame"])
    del simple_data["dataFrame"]
    del restored_dict["dataFrame"]
    assert simple_data == restored_dict
    # dict with pandas series
    series = pd.Series([10, 20, 30, 40], index=["a", "b", "c", "d"])
    simple_series = {
        "aString": "Text",
        "anInt": 1234,
        "aFloat": 1.234,
        "dataSeries": series,
    }
    stored = Bundle.bundle(simple_series)
    restored_dict = Bundle.unpack(stored)
    assert np.all(simple_series["dataSeries"] == restored_dict["dataSeries"])
    del simple_series["dataSeries"]
    del restored_dict["dataSeries"]
    assert simple_series == restored_dict
