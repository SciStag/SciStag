"""
Tests the Anchor2D class
"""
import pytest

from scistag.imagestag import Size2D, Pos2D
from scistag.imagestag.anchor2d import Anchor2D, Anchor2DLiterals
from . import skip_imagestag


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_basics():
    """
    Tests creation and general shifting
    """
    shifting = Anchor2D(Anchor2D.TOP_LEFT).get_position_shift((1.0, 1.0))
    assert shifting == (0, 0)
    shifting = Anchor2D(Anchor2D.BOTTOM_RIGHT).get_position_shift((1.0, 1.0))
    assert shifting == (-1, -1)
    shifting = Anchor2D(Anchor2D.CENTER).get_position_shift((1.0, 1.0))
    assert shifting == (-0.5, -0.5)
    pos = Anchor2D(Anchor2D.CENTER).shift_position(
        pos=Pos2D(4.0, 4.0), size=Size2D(9.0, 9.0)
    )
    assert pos == (-0.5, -0.5)


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_conversion():
    """
    Test literal conversion
    """
    assert Anchor2D(Anchor2D.CENTER) == Anchor2D("c")
    assert Anchor2D(Anchor2D.TOP) == Anchor2D("t")
    assert Anchor2D(Anchor2D.TOP_LEFT) == Anchor2D("topLeft")
    assert Anchor2D(Anchor2D.BOTTOM_RIGHT) == Anchor2D("bottomRight")
    assert Anchor2D(Anchor2D.BOTTOM_RIGHT) == Anchor2D("br")
    with pytest.raises(ValueError):
        assert Anchor2D(Anchor2D.BOTTOM_RIGHT) == Anchor2D("nonsense")
