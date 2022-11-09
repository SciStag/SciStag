"""
Tests the scistag.slidestag.Widget class
"""
import pytest

from scistag.common import ConfigStag
from scistag.imagestag import Canvas, Size2D, Pos2D
from scistag.slidestag import Widget
from unittest.mock import patch

from . import skip_slidestag


@pytest.mark.skipif(skip_slidestag, reason="SlideStag tests disabled")
def test_creation():
    """
    Tests general constructor parameters
    """
    my_widget = Widget()
    assert my_widget.position.to_tuple() == (0, 0)
    assert my_widget.size.to_tuple() == (100, 100)
    my_widget = Widget(position=(23, 45), size=(58, 60))
    assert my_widget.position.to_tuple() == (23, 45)
    assert my_widget.size.to_tuple() == (58, 60)
    my_widget = Widget(position=Pos2D(55, 76), size=Size2D(48, 66))
    assert my_widget.position.to_tuple() == (55, 76)
    assert my_widget.size.to_tuple() == (48, 66)
    sub_widget = Widget()
    my_widget.add_widget(sub_widget)
    with pytest.raises(RuntimeError):
        my_widget.add_widget(sub_widget)
    another_widget = Widget()
    widget_with_parent = Widget(parent=another_widget)
    another_widget_with_parent = Widget(parent=another_widget)
    assert widget_with_parent.parent == another_widget
    another_widget.remove_widget(another_widget_with_parent)
    with patch.object(another_widget, "remove_widget") as call_test:
        another_widget.remove_widget(widget_with_parent)
        assert call_test.called


@pytest.mark.skipif(skip_slidestag, reason="SlideStag tests disabled")
def test_setters():
    """
    Tests if all setter functions trigger correctly
    """
    my_widget = Widget()
    with patch.object(my_widget, "set_position") as call_test:
        my_widget.position = Pos2D(99, 102)
        assert call_test.called
    with patch.object(my_widget, "set_size") as call_test:
        my_widget.size = Size2D(99, 102)
        assert call_test.called
    with patch.object(my_widget, "set_visible") as call_test:
        my_widget.visible = False
        my_widget.visible = True
        assert call_test.called
        assert call_test.call_count == 2
    with patch.object(my_widget, "set_alpha") as call_test:
        my_widget.alpha = 0.5
        assert call_test.called
    my_widget.position = Pos2D(99, 102)
    my_widget.size = Size2D(200, 300)
    my_widget.visible = False
    assert not my_widget.visible
    my_widget.visible = True
    my_widget.alpha = 0.5
    assert my_widget.position.to_tuple() == (99, 102)
    assert my_widget.size.to_tuple() == (200, 300)
    assert my_widget.alpha == 0.5
    with pytest.raises(ValueError):
        my_widget.parent = "AnotherValue"


@pytest.mark.skipif(skip_slidestag, reason="SlideStag tests disabled")
def test_paint():
    canvas = Canvas()
