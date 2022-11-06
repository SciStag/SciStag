import pytest

from . import vl
from scistag.imagestag import Canvas, Colors, HTextAlignment, VTextAlignment
from ...imagestag.anchor2d import Anchor2D
from . import skip_imagestag

@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_font_bounding():
    """
    Test the rect function
    :return:
    """
    vl.test.begin("Testing font bounding, ascend and descend")
    text_off = (128, 128)
    text = "Hello World!"
    canvas = Canvas(size=(256, 256))
    font = canvas.get_default_font()
    canvas.text(pos=text_off, text=text, color=Colors.RED, font=font,
                _show_formatting=True)
    vl.sub_test("Basic Hello world print")
    vl.test.assert_image("canvas_text", canvas,
                    hash_val='efc178b2c22537a01e7f1e610e502e96')
    canvas.clear()
    canvas.text(pos=text_off, text="W ÄÖÜ gy", color=Colors.RED, font=font,
                _show_formatting=True)
    vl.sub_test("Umlauts with normal top-left alignment")
    vl.test.assert_image("canvas_text", canvas,
                    hash_val='70ddbe441578d0c425925e8bf4fe2aac')
    canvas.clear()
    canvas.text(pos=text_off, text="W ÄÖÜ gy", color=Colors.RED, font=font,
                _show_formatting=True, v_align=VTextAlignment.BASELINE)
    vl.sub_test("Umlauts and Baseline alignment")
    vl.test.assert_image("canvas_text", canvas,
                    hash_val='43f1ae99ed848a422c2a62e71b3ab805')
    canvas.clear()
    canvas.text(pos=text_off, text="W abcde", color=Colors.RED, font=font,
                _show_formatting=True, v_align=VTextAlignment.BASELINE)
    vl.sub_test("Baseline w/o umlauts")
    vl.test.assert_image("canvas_text", canvas,
                    hash_val='7ef77be8c2981f40d23e7c21f8736ab9')
    canvas.clear()
    canvas.text(pos=text_off, text=text, color=Colors.RED, font=font,
                h_align=HTextAlignment.CENTER,
                _show_formatting=True)
    vl.sub_test("Horizontally centered alignment")
    vl.test.assert_image("canvas_text", canvas,
                    hash_val='efc178b2c22537a01e7f1e610e502e96')
    multiline_text = "Hello World!\nHow are you\ndoing today?"
    canvas.clear()
    canvas.text(pos=text_off, text=multiline_text, color=Colors.RED, font=font,
                h_align=HTextAlignment.CENTER,
                anchor=Anchor2D.TOP,
                _show_formatting=True)
    vl.sub_test("Multiline text w/ horizontal alignment and top anchor")
    vl.test.assert_image("canvas_text", canvas,
                    hash_val='d16b0b0c32a59cecc4a57d098bee82ab')
    canvas.clear()
    canvas.text(pos=text_off, text=multiline_text, color=Colors.RED, font=font,
                h_align=HTextAlignment.CENTER,
                anchor=Anchor2D.TOP,
                v_align=VTextAlignment.BASELINE,
                _show_formatting=True)
    vl.sub_test("Vertical baseline, horizontal center, top anchor")
    vl.test.assert_image("canvas_text", canvas,
                    hash_val='e787cf2cbfd46954c5ec19b118cc336a')
    canvas.clear()
    canvas.text(pos=text_off, text=multiline_text, color=Colors.RED, font=font,
                h_align=HTextAlignment.CENTER,
                anchor=Anchor2D.CENTER,
                _show_formatting=True)
    vl.sub_test("Horizontal center and center anchor")
    vl.test.assert_image("canvas_text", canvas,
                    hash_val='544f81edad51b62c08952b7f9cae515d')
    canvas.clear()
    vl.sub_test("Multiline text using string literals for h align and anchor")
    canvas.text(pos=text_off, text=multiline_text, color=Colors.RED, font=font,
                h_align="right",
                anchor="cr",
                _show_formatting=True)
    vl.test.assert_image("canvas_text", canvas,
                    hash_val='e63da32b61ef932673e3cc50b2c45c41')
    canvas.clear()
    vl.sub_test("Text using string literals for v align and anchor")
    canvas.text(pos=text_off, text="A bottom aligned text",
                color=Colors.RED, font=font,
                v_align="bottom",
                anchor="tl",
                _show_formatting=True)
    vl.test.assert_image("canvas_text", canvas,
                    hash_val='31785cd02516c18f748014bee11ddfad')
    canvas.clear()
    canvas.text(pos=text_off, text=multiline_text, color=Colors.RED, font=font,
                center=True,
                stroke_color=Colors.WHITE,
                stroke_width=1,
                _show_formatting=True)
    vl.sub_test("Text with 1 pixel stroke")
    vl.test.assert_image("canvas_text", canvas,
                    hash_val='f9c1aa915b24c82901ff781b571547f8')
