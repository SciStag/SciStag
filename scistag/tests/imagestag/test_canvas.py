"""
Tests the :class:`Canvas` class.
"""
import numpy as np
import pytest

from scistag.tests.visual_test_log_scistag import VisualTestLogSciStag
from scistag.imagestag import Colors, Color, Size2D
from scistag.imagestag.canvas import Canvas

from . import vl, skip_imagestag

skip_imagestag_fonts = skip_imagestag
"Defines if font tests shall be skipped"


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_canvas():
    """
    Test construction and base functions
    """
    canvas = Canvas(size=(300, 256))
    assert canvas.width == 300 and canvas.height == 256
    assert canvas.size == (300, 256)


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_rect():
    """
    Test the rect function
    :return:
    """
    vl.test.begin("Testing the canvas rectangle functions")
    vl.sub_test("Drawing a simple red rectangle")
    canvas = Canvas(size=(300, 256))
    canvas.rect((50, 50), (100, 100), color=Colors.RED)
    vl.test.assert_image("rect", canvas, '28b1574bf8893d7c80ec18721966a918')
    vl.sub_test("Painting with a shifted offset")
    canvas = Canvas(size=(300, 256))
    canvas.push_state()
    canvas.add_offset_shift((50, 50))
    canvas.rect((50, 50), (100, 100), outline_color=Colors.CYAN,
                outline_width=2)
    vl.test.assert_image("rect", canvas, '83239b58306da0d8a804da95aa319e59')
    vl.sub_test("Painting at the bounding's limits")
    canvas.pop_state()
    canvas = Canvas(size=(300, 256))
    canvas.rect((-50, -50), (100, 100), color=Colors.DARK_MAGENTA)
    canvas.rect(bounding=((250, 240), (100, 100)), color=Colors.DARK_RED)
    vl.test.assert_image("rect", canvas, '103f9fc339e7d6db708aa78ab50fcbaf')


@pytest.mark.skipif(skip_imagestag_fonts, reason="ImageStag tests disabled")
def test_image_in_image():
    """
    Tests the basic text rendering functionality
    """
    canvas = Canvas(size=(300, 256), default_color=Colors.BLACK)
    sub_canvas = Canvas(size=(200, 200), default_color=Colors.WHITE)
    sub_canvas.text((50, 50), "Hello world!")
    canvas.draw_image(sub_canvas.to_image(), pos=(50, 50))
    vl.test.assert_image("draw_image", canvas,
                         '5945764a21be07673d3b1c5f52dfc741')
    canvas = Canvas(size=(300, 256), default_color=Colors.BLACK)
    canvas.add_offset_shift((50, 50))
    canvas.draw_image(sub_canvas.to_image(), pos=(0, 0))
    vl.test.assert_image("draw_image", canvas,
                         '5945764a21be07673d3b1c5f52dfc741')


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_draw_rectangle_list():
    """
    Tests the draw_rectangle_list function
    :return:
    """
    vl.sub_test("Plotting many rectangles using draw_rectangle_list")
    for outline in [False, True]:
        outline_width = 2 if outline else 0
        canvas = Canvas(size=(300, 256), default_color=Colors.BLACK)
        canvas.add_offset_shift((50, 50))
        rectangles = []
        colors = []
        rect_size = 8
        for step in range(10):
            ox = step * 14
            oy = step * 15
            rectangles.append(((ox, oy), (ox + rect_size, oy + rect_size)))
            colors.append(Color(step * 0.2 + 0.1, 0.0, 0.0).to_int_rgba())
        # base test
        canvas.rectangle_list(rectangles,
                              single_color=Color(Colors.RED).to_int_rgba(),
                              outline_width=outline_width)
        # +ignorevl
        hash_val = "4bf6c0a7525af58085960c93f3756d40" if outline \
            else "844d4af277cbdb8731ecc8a33b62e10c"
        vl.test.assert_image("draw_rectangle_list", canvas, hash_val)
        vl.sub_test("Plotting many rectangles with offset")
        # offset test
        canvas.push_state()
        canvas.clear(Colors.BLACK)
        canvas.add_offset_shift((50, 10))
        canvas.rectangle_list(rectangles,
                              single_color=Color(Colors.RED).to_int_rgba(),
                              outline_width=outline_width)
        canvas.pop_state()
        # +ignorevl
        hash_val = "58fa0d38ceeedf5767f60975ed900583" if outline \
            else "50eb1f31cbcb65206a36eaf95137d72e"
        vl.test.assert_image("draw_rectangle", canvas, hash_val)
        vl.sub_test("Plotting many rectangles with offset "
                    "and different colors")
        # multi color test
        canvas.clear(Colors.BLACK)
        canvas.add_offset_shift((50, 10))
        canvas.rectangle_list(rectangles,
                              colors,
                              outline_width=outline_width)
        # +ignorevl
        hash_val = "b2ca8a2a847d9ffc4092476124e74b5d" if outline \
            else "0eb9e0c61ed35d0aabb35cf713500e58"
        vl.test.assert_image("draw_rectangle", canvas, hash_val)


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_draw_polygon_fill():
    """
    Filled polygon
    """
    vl.sub_test("Rendering polygons")
    canvas = Canvas(size=(128, 128), default_color=Colors.BLACK)
    polygon = [(20, 20), (80, 30), (90, 90), (30, 100)]
    canvas.polygon(polygon, color=Colors.RED)
    hash_val = "3f90539daefb6b3dc60fa8129c1c6377"
    vl.test.assert_image("polygon_convex_fill", canvas, hash_val)


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_draw_polygon_fill_outline():
    """
    Filled polygon with outline
    """
    canvas = Canvas(size=(128, 128), default_color=Colors.BLACK)
    polygon = [(20, 20), (80, 30), (90, 90), (30, 100)]
    canvas.polygon(polygon, color=Colors.RED, outline_color=Colors.BLUE,
                   outline_width=2)
    hash_val = "6af0b5c529594912d9fbae60e1d7bab9"
    vl.test.assert_image("polygon_convex_fill_border", canvas, hash_val)


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_draw_polygon_fill_outline_concave():
    """
    Concave filled polygon with outline
    """
    canvas = Canvas(size=(128, 128), default_color=Colors.BLACK)
    canvas.add_offset_shift((15, 15))
    polygon = np.array([(20, 20), (80, 30), (90, 90), (60, 70), (30, 100)])
    canvas.polygon(polygon, color=Colors.RED, outline_color=Colors.WHITE,
                   outline_width=8)
    hash_val = "7b68caffba93580e75f3079dd0e959bf"
    vl.test.assert_image("polygon_convex_fill_border_concave", canvas, hash_val)


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_draw_lines():
    """
    Lines and multi-lines
    """
    canvas = Canvas(size=(128, 128), default_color=Colors.BLACK)
    line_list = [(20, 20), (80, 30), (90, 90), (60, 70), (30, 100)]
    canvas.line(line_list, color=Colors.RED, width=3)
    hash_val = "69cc3fab0cbaef77fae888186050fb66"
    vl.test.assert_image("line_list", canvas, hash_val)
    # shift line with two points
    canvas.add_offset_shift((15, 15))
    canvas = Canvas(size=(128, 128), default_color=Colors.BLACK)
    line_list = [(20, 20), (80, 30)]
    canvas.line(line_list, color=Colors.RED, width=10, curved_joints=True)
    hash_val = "83e521e68b400fae3f2c476728aecb8e"
    vl.test.assert_image("line_list_two_points", canvas, hash_val)
    # shift line with three points and joint
    canvas = Canvas(size=(128, 128), default_color=Colors.BLACK)
    canvas.add_offset_shift((15, 15))
    line_list = np.array([(20, 20), (80, 30), (100, 80)])
    canvas.line(line_list, color=Colors.RED, width=10, curved_joints=True)
    hash_val = "a1ebba1a8b202b07f7b4a039b384df17"
    vl.test.assert_image("line_list_three_points", canvas, hash_val)


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_draw_circles():
    """
    Circles
    """
    canvas = Canvas(size=(128, 128), default_color=Colors.BLACK)
    canvas.circle((70, 70), radius=30, color=Colors.RED)
    hash_val = "dbcc979c2e855e1b0f5efde1d394dfbb"
    vl.test.assert_image("circle", canvas, hash_val)
    # shifted and as ellipse
    canvas.add_offset_shift((15, 15))
    canvas = Canvas(size=(128, 128), default_color=Colors.BLACK)
    canvas.circle((70, 70), radius=(40, 20), color=Colors.RED)
    hash_val = "81dc4f4c659a9c4867f413470a8f299f"
    vl.test.assert_image("ellipse", canvas, hash_val)
    # with outline
    canvas = Canvas(size=(128, 128), default_color=Colors.BLACK)
    canvas.add_offset_shift((15, 15))
    canvas.circle((70, 70), size=Size2D(80, 40), outline_color=Colors.BLUE,
                  outline_width=3)
    hash_val = "751338bf0aeebf031e19c2cf7eba0a2e"
    vl.test.assert_image("ellipse_outline", canvas, hash_val)
