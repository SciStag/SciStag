"""
Implements the tests for the checkerbaord shape
"""

from scistag.imagestag import Colors
from scistag.imagestag.canvas import Canvas
from scistag.shapestag.checkerboard import Checkerboard
from scistag.tests.visual_test_log_scistag import VisualTestLogSciStag

from . import vl


def test_checkerboard():
    """
    Tests the checkerboard class
    """
    vl.test.begin("Examples for basic shapes")
    vl.sub_test("A checkerboard using a specified region")
    canvas = Canvas(size=(300, 256), default_color=Colors.BLACK)

    cb = Checkerboard(bounding=(0, 0, 300, 256), tile_size=10)
    cb.draw(canvas)
    vl.test.assert_image("checkerboard", canvas, "789f08e4816cf6df8d9d253c1e649d03")

    # with offset
    vl.sub_test("A checkerboard using a specified region and starting at an offset")
    canvas.clear(Colors.BLACK)
    cb = Checkerboard(bounding=(15.0, 15.0, 300, 256), tile_size=30)
    cb.draw(canvas)
    vl.test.assert_image("checkerboard", canvas, "fd841083202be231b16da6c9b5ae1dba")
    vl.sub_test("A checkerboard with a specified " "column and row count")
    canvas.clear(Colors.BLACK)
    cb = Checkerboard(col_row_count=(16, 10), tile_size=16)
    cb.draw(canvas)
    vl.test.assert_image("checkerboard", canvas, "9b12fce0a2d5add3bbc8b2c1634557bf")
    vl.sub_test(
        "A checkerboard with a specified " "column and row count and custom colors"
    )
    cb = Checkerboard(
        col_row_count=(14, 14), tile_size=20, color_a="#FFEEEE", color_b="#999999"
    ).to_image()
    vl.test.assert_image("checkerboard", cb, "4abd42ecb2be7c39466fc23d78a1b425")
    vl.sub_test(
        "A checkerboard with a specified "
        "column and row count and a negative painting offset"
    )
    cb = Checkerboard(
        col_row_count=(14, 14),
        tile_size=20,
        color_a="#FFEEEE",
        color_b="#999999",
        offset=(-10, -10),
    ).to_image()

    vl.test.assert_image("checkerboard", cb, "4abd42ecb2be7c39466fc23d78a1b425")
