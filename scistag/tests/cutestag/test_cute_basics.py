"""
Tests the module basics
"""

from scistag.cutestag import cute_available, get_cute


def test_loading():
    """
    Tests loading and detection
    """
    is_available = cute_available()
    handle = get_cute()
    assert (not is_available and handle is None) or (
                is_available and handle is not None)
