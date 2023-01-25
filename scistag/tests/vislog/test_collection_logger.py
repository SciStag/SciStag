"""
Tests the logging of lists and dictionaries
"""

from . import vl


def test_list():
    """
    Tests the logging of lists
    """
    vl.test.checkpoint("vislog.list")
    vl.collection.add(
        [1, 2, 3, "a", 123.4, ["A", "B", "C", {"adict": {"withADict": {"value": 123}}}]]
    )
    vl.add([4, 5, 6])
    vl.test.assert_cp_diff("2bfc775c38423ab9e7a98f6eb6044fff")


def test_dict():
    """
    Tests the logging of a dictionary
    """
    vl.test.checkpoint("vislog.dict")
    new_dict = {
        "firstName": "John",
        "lastName": "Doe",
        "registered": True,
        "lastOrderAmount": 19.45,
        "customerNumber": 84232323,
        "orderIds": [1234, 5678],
    }
    vl.collection(new_dict)
    vl.test.assert_cp_diff("1a8c344aa266a2ca3403121ea6ee974d")
    vl.test.checkpoint("vislog.dict_add")
    vl.add(new_dict)
    vl.test.assert_cp_diff("1a8c344aa266a2ca3403121ea6ee974d")


nested_dict = {
    "attributes": {"quality": "awesome", "background": None, "error": False},
    "objects": [
        [
            [2629.660679168288, 1801.1979619022416],
            [3401.483733557142, 1801.1979619022416],
            [3401.483733557142, 2076.964978686819],
            [2629.660679168288, 2076.964978686819],
        ]
    ],
    "object_boundings": [
        [
            [2629.660679168288, 1801.1979619022416],
            [3401.483733557142, 2076.964978686819],
        ]
    ],
    "outer_bounding": [
        [2629.660679168288, 1801.1979619022416],
        [3401.483733557142, 2076.964978686819],
    ],
    "test_list": [{"name": "Michael", "age": "23"}, {"name": "Steven", "age": "23"}],
    "sub_objects": [],
    "resolution": [6000, 4545],
    "cell": [0, 1],
}


def test_complex_list():
    """
    Tests the logging of a nested dictionary
    """
    vl.test.checkpoint("vislog.nested_dict")
    vl.collection(nested_dict)
    vl.test.assert_cp_diff("b25eacbd43a27eb8d033e12e562d6d86")
