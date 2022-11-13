"""
Tests the logging of lists and dictionaries
"""

from . import vl


def test_list():
    """
    Tests the logging of lists
    """
    vl.test.checkpoint("vislog.list")
    vl.log_list(
        [1, 2, 3, "a", 123.4,
         ["A", "B", "C", {"adict": {"withADict": {"value": 123}}}]])
    vl.add([4, 5, 6])
    vl.test.assert_cp_diff('e7a636f66ba4f77a536641bee7bc17f1')


def test_dict():
    """
    Tests the logging of a dictionary
    """
    vl.test.checkpoint("vislog.dict")
    new_dict = {"firstName": "John",
                "lastName": "Doe",
                "registered": True,
                "lastOrderAmount": 19.45,
                "customerNumber": 84232323,
                "orderIds": [1234, 5678]
                }
    vl.log_dict(new_dict)
    vl.test.assert_cp_diff("d7a84ee5a7e175a1cf9d6205c284e48c")
    vl.test.checkpoint("vislog.dict_add")
    vl.add(new_dict)
    vl.test.assert_cp_diff("d7a84ee5a7e175a1cf9d6205c284e48c")
