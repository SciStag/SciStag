import pytest
import time
import numpy as np
from scistag.tests.datastag.datastag4flask.shared_test_client import test_client, test_remote_connection
from scistag.tests.datastag.datastag4flask.shared_data_dummies import get_dummy_jpg, get_dummy_np_array, get_dummy_dict


def test_set_set(test_remote_connection):
    """
    Setting and getting values directly using get and set
    """
    trc = test_remote_connection
    string_value = "Hello stags!"
    dummy_jpg = get_dummy_jpg()
    # base types
    assert trc.set("testValue", string_value)
    assert trc.get("testValue") == string_value
    assert trc.get("testValueNotExisting", 123) == 123
    assert trc.set("testValue", string_value)
    assert trc.set("testNumber", 456)
    assert trc.get("testNumber") == 456
    assert trc.set("testFloat", 4.56)
    assert trc.get("testFloat") == 4.56
    assert trc.set("testBool", True)
    assert trc.get("testBool")
    # timeout
    to_value = "Running stag"
    to_time = 0.1
    assert trc.set("testValueWithTimeout", to_value, timeout_s=to_time)
    read_value = trc.get("testValueWithTimeout", default=456)
    assert read_value == to_value
    time.sleep(to_time)
    assert trc.get("testValueWithTimeout", default=456) == 456
    # dict
    a_dict = get_dummy_dict()
    trc.set("testDict", a_dict)
    assert trc.get("testDict") == a_dict
    # advanced types (bytes + numpy)
    trc.set("Jpeg", dummy_jpg)
    read_jpg = trc.get("Jpeg")
    assert read_jpg == dummy_jpg
    dummy_np = get_dummy_np_array()
    trc.set("Np", dummy_np)
    read_np = trc.get("Np")
    assert np.array_equal(dummy_np, read_np)
