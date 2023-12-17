"""
Tests the comparison widget
"""
import pytest

from scistag.imagestag import Image, Colors
from scistag.vislog.widgets import LComparison
from .. import vl


def test_comparison_init():
    """
    Tests the initializer
    """
    vl.test.begin("Comparison widget (black gray)")

    image_a = Image(size=(128, 128), bg_color=Colors.BLACK, pixel_format="RGBA")
    image_b = Image(size=(128, 128), bg_color=Colors.GRAY)
    vl.test.checkpoint("comparison_black_gray")
    LComparison(
        vl, [image_a, image_b], style=LComparison.Style.HOR_SPLIT, name="testComp"
    )
    vl.test.assert_cp_diff("9d2044f4dcf1aea7462a5f581be886f1")
    vl.flush()
    with pytest.raises(ValueError):
        LComparison(vl, [image_a, image_b], style="nonsense")
    LComparison(vl, [image_a, image_b], style=LComparison.Style.HOR_SPLIT, insert=False)
    LComparison(vl, [], style=LComparison.Style.HOR_SPLIT)
    LComparison(vl, [image_a], style=LComparison.Style.HOR_SPLIT)
    with pytest.raises(ValueError):
        LComparison(vl, ["sausage"], style=LComparison.Style.HOR_SPLIT)
