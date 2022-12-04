"""
Tests the class :class:`StagApp` which provides functions for the application
lifecycle management
"""
import sys

from scistag.common import StagApp


def test_main():
    """
    Tests the entry point detection
    """
    assert not StagApp.is_main()
    old_main = sys.modules["__main__"]
    sys.modules["__main__"] = sys.modules[__name__]
    assert StagApp.is_main()
    sys.modules["__main__"] = old_main
