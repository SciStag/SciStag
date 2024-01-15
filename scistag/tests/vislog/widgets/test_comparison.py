"""
Tests the comparison widget
"""
import pytest

from scistag.imagestag import Image, Colors
from scistag.vislog import VisualLog
from scistag.vislog.widgets import LComparison
from .. import vl


def test_comparison_init():
    """
    Tests the initializer
    """
    vl.test.begin("Comparison widget (black gray)")

    image_a = Image(size=(128, 128), bg_color=Colors.BLACK, pixel_format="RGBA")
    image_b = Image(size=(128, 128), bg_color=Colors.GRAY)

    options = VisualLog.setup_options()
    options.page.session_id ="comp_test"
    sub_log = VisualLog(
        options=options,
    )

    sub_log.default_builder.test.checkpoint("comparison_black_gray")

    LComparison(
        vl, [image_a, image_b], style=LComparison.Style.HOR_SPLIT, name="testComp"
    )
    sub_log.default_builder.test.assert_cp_diff("d41d8cd98f00b204e9800998ecf8427e")
    vl.flush()
    with pytest.raises(ValueError):
        LComparison(vl, [image_a, image_b], style="nonsense")
    LComparison(vl, [image_a, image_b], style=LComparison.Style.HOR_SPLIT, insert=False)
    LComparison(vl, [], style=LComparison.Style.HOR_SPLIT)
    LComparison(vl, [image_a], style=LComparison.Style.HOR_SPLIT)
    with pytest.raises(ValueError):
        LComparison(vl, ["sausage"], style=LComparison.Style.HOR_SPLIT)
