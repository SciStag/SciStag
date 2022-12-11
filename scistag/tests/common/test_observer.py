"""
Tests the Observer and ObserverList class
"""
import time

import pytest

from scistag.common import Observer, ObserverList


class ObserverMock(Observer):
    def __init__(self, refresh_time_s=0.1):
        super().__init__(refresh_time_s=refresh_time_s)
        self.value = "123"

    def hash_int(self) -> str:
        return self.value


def test_observer():
    """
    Tests the observer functionalities
    """
    base_class = Observer()
    with pytest.raises(NotImplementedError):
        base_class.__hash__()
    mock = ObserverMock(refresh_time_s=0.05)
    mock.value = "456"
    assert mock.__hash__() == "456"
    mock.value = "789"
    assert mock.__hash__() == "456"  # still cached?
    time.sleep(0.05)
    assert mock.__hash__() == "789"


def test_observer_list():
    """
    Tests the ObserverList
    """
    mock_a = ObserverMock(refresh_time_s=0.05)
    mock_a.value = "cka"
    mock_b = ObserverMock(refresh_time_s=0.05)
    mock_b.value = "rfc"
    mock_c = ObserverMock(refresh_time_s=0.05)
    mock_c.value = "jkl"
    mock_d = ObserverMock(refresh_time_s=0.05)
    mock_d.value = "fkh"
    obs_list = ObserverList([mock_a], refresh_time_s=0.05)
    cur = obs_list.__hash__()
    assert cur == "64fcb4b683ee7bebcfa76d99d94fcaf2"
    assert obs_list.__hash__() == cur
    obs_list.add(mock_b)
    assert obs_list.__hash__() == "d99f1b7c4aafd45b22eb6a46efad26d9"
    obs_list.add([mock_c, mock_d])
    assert obs_list.__hash__() == "556e77c9d7228d6126073ccb4595ab52"
    mock_d.value = "ZZK"  # still cached
    assert obs_list.__hash__() == "556e77c9d7228d6126073ccb4595ab52"
    time.sleep(0.05)
    assert not obs_list.__hash__() == "556e77c9d7228d6126073ccb4595ab52"
