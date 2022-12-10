"""
Tests the logging of lists and dictionaries
"""

from . import vl


def test_list():
    """
    Tests the logging of lists
    """
    vl.test.checkpoint("vislog.list")
    vl.collection.log(
        [1, 2, 3, "a", 123.4,
         ["A", "B", "C", {"adict": {"withADict": {"value": 123}}}]])
    vl.add([4, 5, 6])
    vl.test.assert_cp_diff('010a92ee2d44a5b896c10b88926d369b')


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
    vl.collection(new_dict)
    vl.test.assert_cp_diff('b21dae6e811559fab642fae81f5dd299')
    vl.test.checkpoint("vislog.dict_add")
    vl.add(new_dict)
    vl.test.assert_cp_diff("b21dae6e811559fab642fae81f5dd299")


nested_dict = {
    "attributes": {
        "quality": "awesome",
        "background": None,
        "error": False
    },
    "objects": [
        [
            [
                2629.660679168288,
                1801.1979619022416
            ],
            [
                3401.483733557142,
                1801.1979619022416
            ],
            [
                3401.483733557142,
                2076.964978686819
            ],
            [
                2629.660679168288,
                2076.964978686819
            ]
        ]
    ],
    "object_boundings": [
        [
            [
                2629.660679168288,
                1801.1979619022416
            ],
            [
                3401.483733557142,
                2076.964978686819
            ]
        ]
    ],
    "outer_bounding": [
        [
            2629.660679168288,
            1801.1979619022416
        ],
        [
            3401.483733557142,
            2076.964978686819
        ]
    ],
    "test_list": [
        {"name": "Michael",
         "age": "23"},
        {"name": "Steven",
         "age": "23"}
    ],
    "sub_objects": [],
    "resolution": [
        6000,
        4545
    ],
    "cell": [
        0,
        1
    ]
}


def test_complex_list():
    """
    Tests the logging of a nested dictionary
    """
    vl.test.checkpoint("vislog.nested_dict")
    vl.collection(nested_dict)
    vl.test.assert_cp_diff("c6028167a50731299783411d20465d8a")
