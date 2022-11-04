"""
Tests the scistag.common.Component class
"""

from typing import Tuple

import pytest
from unittest.mock import patch
import pandas as pd

from scistag.common import Component


class AWidget(Component):
    def __init__(self):
        super().__init__()
        self.x = 0.0
        "A widget's y coordinate relative to it's parent's left border"
        self.y = 0.0
        "A widget's x coordinate relative to it's parent's top border"
        self.position = (0.0, 0.0)
        "A widget's position, relative to it's parent's top left border"
        self.size = (100.0, 100.0)
        "A widget's size in pixels"
        self.parent = None
        "(read-only). A widget's parent widget"
        self.properties = self.PROPERTIES

    PROPERTIES = {"x": {"info": "A widget's x coordinate in pixels", "type": float},
                  "y": {"info": "A widget's y coordinate in pixels", "type": float},
                  "position": {"info": "A widget's position in pixels, relative to it's parents upper left coordinate",
                               "type": tuple[float, float]},
                  "size": {"info": "A widget's size in pixels", "type": tuple[float, float]},
                  "parent": {"info": "A widget's parent widget", "type": "AWidget", "readOnly": True}
                  } | Component.PROPERTIES

    def set_x(self, value):
        """
        Sets a new x coordinate - the offset on the x axis relative to it's parent's left bounding
        :param value: The new value in pixels
        """
        self.set_position((value, self.y))

    def set_y(self, value):
        """
        Sets a new y coordinate - the offset on the y axis relative to it's parent's top bounding
        :param value: The new value in pixels
        """
        self.set_position((self.x, value))

    def set_position(self, value):
        """
        Sets a new y coordinate - the offset on the y axis relative to it's parent's top bounding
        :param value: The new value in pixels
        """
        value = float(value[0]), float(value[1])
        self.__dict__['position'] = value
        self.__dict__['x'] = value[0]
        self.__dict__['y'] = value[1]


def test_properties():
    """
    Tests the Component's property definition, get and set functionality
    """
    widget = AWidget()
    assert widget.position == (0.0, 0.0)
    with patch.object(AWidget, "set_x") as call_test:
        widget.x = 456
        assert call_test.called
    with patch.object(AWidget, "set_y") as call_test:
        widget.y = 456
        assert call_test.called
    widget.x = 123
    assert widget.x == 123
    assert widget.position == (123.0, 0.0)
    with pytest.raises(ValueError):  # should fail, not allowed as it is read-only
        widget.parent = object()


class CacheTestClass(Component):
    """
    Example class for the automatic unloading of data created during the execution of handle_load
    """

    def __init__(self, forget_load=False, forget_unload=False):
        super().__init__()
        self.x = 123
        self.forget_load = forget_load
        self.forget_unload = forget_unload
        self.temp_data = None
        self.add_volatile_member("temp_data")

    def handle_load(self):
        if not self.forget_load:
            super().handle_load()
        self.temp_data = "Some dynamic loaded data"
        assert self.get_is_loading()
        self["db"] = pd.DataFrame(columns=['a', 'b'])
        self["otherDb"] = pd.DataFrame(columns=['a', 'b'])
        with pytest.raises(ValueError):
            self[".someValue"] = 1

    def handle_unload(self):
        if not self.forget_unload:
            super().handle_unload()


def test_cache():
    """
    Tests the correct cleansing of the cache and of member variables assigned during the load process.
    """
    test_object = CacheTestClass()
    assert "db" not in test_object
    test_object.load()
    assert "db" in test_object  # test __contains__
    my_db = test_object['db']  # test __getitem__
    assert my_db is not None
    assert isinstance(my_db, pd.DataFrame)
    assert "otherDb" in test_object
    other_db = test_object["otherDb"]
    assert isinstance(other_db, pd.DataFrame)
    del test_object["otherDb"]  # test __delitem__
    with pytest.raises(KeyError):
        del test_object["invalidValue"]
    with pytest.raises(KeyError):
        _ = test_object["otherInvalidValue"]
    assert "otherDb" not in test_object
    assert test_object.temp_data == "Some dynamic loaded data"
    test_object.unload()
    # volatile data should not be existing anymore, registered member variables should be empty
    assert "db" not in test_object
    assert test_object.temp_data is None
    assert test_object.x == 123


def test_load_unload():
    """
    Tests the correct executing of the load, unload, handle_load and handle_unload methods.
    """
    # test missing handle_load
    test_object_load = CacheTestClass(forget_load=True)
    with pytest.raises(RuntimeError):
        test_object_load.load()
    # test missing handle_unload
    test_object_unload = CacheTestClass(forget_unload=True)
    test_object_unload.load()
    with pytest.raises(RuntimeError):
        test_object_unload.unload()
    # test unload before load
    test_object_too_early_unload = CacheTestClass()
    with pytest.raises(RuntimeError):
        test_object_too_early_unload.unload()
    # test twice loaded
    test_object_load_twice = CacheTestClass()
    test_object_load_twice.load()
    with pytest.raises(RuntimeError):
        test_object_load_twice.load()
