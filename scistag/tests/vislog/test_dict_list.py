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
    vl.test.assert_cp_diff('15f856f69e1af9ec32408989466b3e4f')


def test_dict():
    """
    Tests the logging of a dictionary
    """
    vl.test.checkpoint("vislog.dict")
    vl.log_dict({"firstName": "John",
                 "lastName": "Doe",
                 "registered": True,
                 "lastOrderAmount": 19.45,
                 "customerNumber": 84232323,
                 "orderIds": [1234, 5678]
                 })
    vl.test.assert_cp_diff("d7a84ee5a7e175a1cf9d6205c284e48c")
