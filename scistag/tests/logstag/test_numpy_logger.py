"""
Tests the numpy logging functions
"""

from unittest import mock

import numpy as np
import pytest

from . import vl


def test_np_assert():
    """
    Tests numpy assertion
    """
    # testing numpy assertion
    np_array = np.ones((4, 4), dtype=float)
    with mock.patch('builtins.print'):
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

    vl.test.assert_np("test_np_array", np_array, rounded=2,
                      hash_val="99140a9b8e68954a484e0de3c6861fc6")
    np_array[0][1] = 0.99
    vl.test.assert_np("test_np_array", np_array, rounded=2,
                      hash_val="99140a9b8e68954a484e0de3c6861fc6")
    np_array[0][1] = 0.98
    with pytest.raises(AssertionError):
        vl.test.assert_np("test_np_array", np_array, rounded=2,
                          hash_val="99140a9b8e68954a484e0de3c6861fc6")
