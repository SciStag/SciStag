import numpy as np
from scistag.tests.datastag.datastag4flask.shared_test_client import \
    test_client, test_remote_connection
from scistag.tests.datastag.datastag4flask.shared_data_dummies import \
    get_dummy_jpg, get_dummy_np_array, get_dummy_dict


def test_push_pop_len(test_remote_connection):
    trc = test_remote_connection
    dummy_jpg = get_dummy_jpg()
    assert trc.push("testPpList", 123)
    assert trc.pop("testPpList") == 123
    assert trc.llen("testPpList") == 0
    assert trc.pop("testPpList") is None
    assert trc.pop("testPpList", default=123) == 123
    assert trc.push("testPpList", 123)
    assert trc.push("testPpList", 456)
    assert trc.push("testPpList", 789)
    assert trc.llen("testPpList") == 3
    assert trc.pop("testPpList", index=1) == 456
    assert trc.llen("testPpList") == 2
    dummy_dict = get_dummy_dict()
    assert trc.push("otherPpList", [123, dummy_dict])
    assert trc.pop("otherPpList") == 123
    assert trc.pop("otherPpList") == dummy_dict
    # bytes & numpy
    assert trc.push("aJpeg", dummy_jpg)
    assert trc.pop("aJpeg") == dummy_jpg
    np_array = get_dummy_np_array(fill_value=3)
    assert trc.push("aNumpyList", np_array)
    assert np.array_equal(trc.pop("aNumpyList"), np_array)


def test_lelements(test_remote_connection):
    trc = test_remote_connection
    data_list = [123, "456", True, {"test": "Value"}]
    for element in data_list:
        assert trc.push("leList", element)
    values = trc.lelements("leList")
    assert values == data_list
    values = trc.lelements("leList", start=2)
    assert values == data_list[2:]
    values = trc.lelements("leList", start=1, end=3)
    assert values == data_list[1:3]
    values = trc.lelements("leList", start=23)
    assert values == []
