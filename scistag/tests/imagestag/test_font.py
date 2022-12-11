import pytest

from . import vl
from scistag.imagestag import Canvas, Colors, HTextAlignment, VTextAlignment
from ...imagestag.anchor2d import Anchor2D
from . import skip_imagestag

skip_imagestag_fonts = skip_imagestag
"Defines if font tests shall be skipped"


@pytest.mark.skipif(skip_imagestag_fonts, reason="ImageStag tests disabled")
def test_font_bounding():
    """
    Test the rect function
    :return:
    """
    vl.test.begin("Testing font bounding, ascend and descend")
    text_off = (128, 128)
    text = "Hello World!"
    canvas = Canvas(size=(256, 256))
    font_small = canvas.get_default_font(size=13)
    assert font_small.size == 13
    font = canvas.get_default_font()
    canvas.text(
        pos=text_off, text=text, color=Colors.RED, font=font, _show_formatting=True
    )
    vl.sub_test("Basic Hello world print")
    vl.test.assert_image(
        "canvas_text", canvas, hash_val="b14dbd65b4c6f87ac0fa0f4e5d75c972"
    )
    canvas.clear()
    canvas.text(
        pos=text_off,
        text="W ÄÖÜ gy",
        color=Colors.RED,
        font=font,
        _show_formatting=True,
    )
    vl.sub_test("Umlauts with normal top-left alignment")
    vl.test.assert_image(
        "canvas_text", canvas, hash_val="85c3b3902ba896872e6f1c6d4f7e45e1"
    )
    canvas.clear()
    canvas.text(
        pos=text_off,
        text="W ÄÖÜ gy",
        color=Colors.RED,
        font=font,
        _show_formatting=True,
        v_align=VTextAlignment.BASELINE,
    )
    vl.sub_test("Umlauts and Baseline alignment")
    vl.test.assert_image(
        "canvas_text", canvas, hash_val="19e7591a1e6aeb0eb33dd25046bce581"
    )
    canvas.clear()
    canvas.text(
        pos=text_off,
        text="W abcde",
        color=Colors.RED,
        font=font,
        _show_formatting=True,
        v_align=VTextAlignment.BASELINE,
    )
    vl.sub_test("Baseline w/o umlauts")
    vl.test.assert_image(
        "canvas_text", canvas, hash_val="9baee1684a58de41c2c983729b5c434c"
    )
    canvas.clear()
    canvas.text(
        pos=text_off,
        text=text,
        color=Colors.RED,
        font=font,
        h_align=HTextAlignment.CENTER,
        _show_formatting=True,
    )
    vl.sub_test("Horizontally centered alignment")
    vl.test.assert_image(
        "canvas_text", canvas, hash_val="b14dbd65b4c6f87ac0fa0f4e5d75c972"
    )
    multiline_text = "Hello World!\nHow are you\ndoing today?"
    canvas.clear()
    canvas.text(
        pos=text_off,
        text=multiline_text,
        color=Colors.RED,
        font=font,
        h_align=HTextAlignment.CENTER,
        anchor=Anchor2D.TOP,
        _show_formatting=True,
    )
    vl.sub_test("Multiline text w/ horizontal alignment and top anchor")
    vl.test.assert_image(
        "canvas_text", canvas, hash_val="6d4de9e99418eae8d0e7bbcf18ac1258"
    )
    canvas.clear()
    canvas.text(
        pos=text_off,
        text=multiline_text,
        color=Colors.RED,
        font=font,
        h_align=HTextAlignment.CENTER,
        anchor=Anchor2D.TOP,
        v_align=VTextAlignment.BASELINE,
        _show_formatting=True,
    )
    vl.sub_test("Vertical baseline, horizontal center, top anchor")
    vl.test.assert_image(
        "canvas_text", canvas, hash_val="3bbcf9cc24c21e3cb2bb6131f6660e3b"
    )
    canvas.clear()
    canvas.text(
        pos=text_off,
        text=multiline_text,
        color=Colors.RED,
        font=font,
        h_align=HTextAlignment.CENTER,
        anchor=Anchor2D.CENTER,
        _show_formatting=True,
    )
    vl.sub_test("Horizontal center and center anchor")
    vl.test.assert_image(
        "canvas_text", canvas, hash_val="32d25897c7e06732f16df54bd79654e7"
    )
    canvas.clear()
    vl.sub_test("Multiline text using string literals for h align and anchor")
    canvas.text(
        pos=text_off,
        text=multiline_text,
        color=Colors.RED,
        font=font,
        h_align="right",
        anchor="cr",
        _show_formatting=True,
    )
    vl.test.assert_image(
        "canvas_text", canvas, hash_val="28e8c7e960f07711a4228ef98823b196"
    )
    canvas.clear()
    vl.sub_test("Text using string literals for v align and anchor")
    canvas.text(
        pos=text_off,
        text="A bottom aligned text",
        color=Colors.RED,
        font=font,
        v_align="bottom",
        anchor="tl",
        _show_formatting=True,
    )
    vl.test.assert_image(
        "canvas_text", canvas, hash_val="613419872ae15b7f711aca2f2244e7af"
    )
    canvas.clear()
    canvas.text(
        pos=text_off,
        text=multiline_text,
        color=Colors.RED,
        font=font,
        center=True,
        stroke_color=Colors.WHITE,
        stroke_width=1,
        _show_formatting=True,
    )
    vl.sub_test("Text with 1 pixel stroke")
    vl.test.assert_image(
        "canvas_text", canvas, hash_val="29f469094776ef15d7176f9e846dd023"
    )
