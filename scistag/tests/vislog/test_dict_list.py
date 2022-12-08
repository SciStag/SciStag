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
    vl.test.assert_cp_diff('1e71f6376cd72e1f5c7bc52199f66d1f')


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
    vl.test.assert_cp_diff('0c1ae1ab8ae88aba31308d4837b51156')
    vl.test.checkpoint("vislog.dict_add")
    vl.add(new_dict)
    vl.test.assert_cp_diff("0c1ae1ab8ae88aba31308d4837b51156")
