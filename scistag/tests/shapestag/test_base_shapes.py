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
    vl.test.assert_image("checkerboard", canvas, "5559fd4635350f823434b37da31b6f4e")

    # with offset
    vl.sub_test("A checkerboard using a specified region and starting at an offset")
    canvas.clear(Colors.BLACK)
    cb = Checkerboard(bounding=(15.0, 15.0, 300, 256), tile_size=30)
    cb.draw(canvas)
    vl.test.assert_image("checkerboard", canvas, "212dc3bd9697b20e2117a86193495bea")
    vl.sub_test("A checkerboard with a specified " "column and row count")
    canvas.clear(Colors.BLACK)
    cb = Checkerboard(col_row_count=(16, 10), tile_size=16)
    cb.draw(canvas)
    vl.test.assert_image("checkerboard", canvas, "51b6fd23a7af332fd72bf2ad33aeb02e")
    vl.sub_test(
        "A checkerboard with a specified " "column and row count and custom colors"
    )
    cb = Checkerboard(
        col_row_count=(14, 14), tile_size=20, color_a="#FFEEEE", color_b="#999999"
    ).to_image()
    vl.test.assert_image("checkerboard", cb, "240be440718718180babb8af5ecfd955")
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

    vl.test.assert_image("checkerboard", cb, "240be440718718180babb8af5ecfd955")
