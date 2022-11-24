"""
Tests the color class
"""
import numpy as np
import pytest

from scistag.imagestag import Color, Colors
from . import skip_imagestag


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_color_basics():
    """
    Tests the color basic functions
    :return:
    """
    color = Color(Colors.WHITE)
    assert color.r == 1.0 and color.g == 1.0 and color.b == 1.0 \
           and color.a == 1.0
    assert str(color) == "Color(1.0,1.0,1.0)"
    color = Color((0.2, 0.3, 0.4, 0.5))
    assert str(color) == "Color(0.2,0.3,0.4,0.5)"
    assert color.to_rgb() == (0.2, 0.3, 0.4)
    assert color.to_rgba() == (0.2, 0.3, 0.4, 0.5)
    assert color.to_int_rgb() == (51, 76, 102)
    assert color.to_int_rgba() == (51, 76, 102, 128)
    color = Color(red=0.2, green=0.3, blue=0.4, alpha=0.5)
    assert color.to_rgba() == (0.2, 0.3, 0.4, 0.5)
    color = Color(color)
    assert color.to_rgba() == (0.2, 0.3, 0.4, 0.5)
    with pytest.raises(RuntimeError):
        color.r = 0.5
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        Color((0.2, 0.3, 0.4, 0.5, 0.6))
    assert Color((0.0, 0.0, 1.0)) == Colors.BLUE
    assert Color("#AABBCCAB").to_rgba() == pytest.approx(
        (0.66, 0.73, 0.8, 0.67), 0.02)
    with pytest.raises(ValueError):
        Color("whatever")
    assert Color(color) == color
    assert Color(color) != Colors.WHITE
    with pytest.raises(ValueError):
        Color(None)
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        Color(np.zeros((5, 3)))
    assert Color((255, 255, 255, 255)) == Colors.WHITE
    assert Color((255, 255, 255)) == Colors.WHITE
    assert Color((255, 0, 255, 255)) == Colors.FUCHSIA
    # test passing colors as rgb int
    assert Color(255, 255, 255) == Color((255, 255, 255))
    assert Color(255, 255, 255, 127 / 255) == Color(255, 255, 255, 127)
