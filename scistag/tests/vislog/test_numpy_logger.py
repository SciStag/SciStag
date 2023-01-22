"""
Tests the numpy logging functions
"""

from unittest import mock

import numpy
import numpy as np
import pytest

from . import vl


def test_np_assert():
    """
    Tests numpy assertion
    """
    # testing numpy assertion
    np_array = np.ones((4, 4), dtype=float)
    with mock.patch("builtins.print"):
        vl.test.assert_np("test_np_array", np_array, dump=True)
    with pytest.raises(AssertionError):
        vl.test.assert_np("test_np_array_no_data", np_array)
    vl.test.assert_np("test_np_array", np_array, variance_abs=0.01)
    vl.test.assert_val("test_np_array", np_array)
    np_array[0][1] = 0.9999
    vl.test.assert_np("test_np_array", np_array, variance_abs=0.01)
    with pytest.raises(AssertionError):
        vl.test.assert_np("test_np_array", np_array, variance_abs=0.00001)
    with pytest.raises(AssertionError):
        np_array[0][1] = 0.9999
        vl.test.assert_np("test_np_array", np_array)

    with pytest.raises(NotImplementedError):
        vl.test.assert_np("test_np_array", np_array, hash_val="123")

    vl.test.assert_np(
        "test_np_array",
        np_array,
        rounded=2,
        hash_val="99140a9b8e68954a484e0de3c6861fc6",
    )
    np_array[0][1] = 0.99
    vl.test.assert_np(
        "test_np_array",
        np_array,
        rounded=2,
        hash_val="99140a9b8e68954a484e0de3c6861fc6",
    )
    np_array[0][1] = 0.98
    with pytest.raises(AssertionError):
        vl.test.assert_np(
            "test_np_array",
            np_array,
            rounded=2,
            hash_val="99140a9b8e68954a484e0de3c6861fc6",
        )


def test_np_logging():
    """
    Tests the basic logging of numpy arrays and vectors
    """
    vl.test.begin("Numpy single line vector")
    vl.test.checkpoint("numpy.basics")
    vl.np(numpy.array([1, 2, 3, 4, 5]))
    vl.test.begin("Numpy single row matrix")
    vl.np(numpy.array([[1, 2, 3, 4, 5]]))
    vl.test.begin("Numpy single column matrix")
    vl.np(numpy.array([[1], [2], [3], [4], [5]]))
    vl.test.begin("Numpy matrix")
    vl.np(np.identity(3), max_digits=4)
    vl.test.assert_cp_diff("dd5cee85b90d64dfa766e87e35aa2453")
    vl.test.checkpoint("numpy.add")
    vl.add(np.identity(3))
    vl.test.assert_cp_diff("a1be9e9a6082cd9769a6f62b428b4f9a")

    with pytest.raises(ValueError):
        vl.np(np.zeros((128, 128)))

    with pytest.raises(ValueError):
        vl.np(np.zeros((20, 20, 20)))
