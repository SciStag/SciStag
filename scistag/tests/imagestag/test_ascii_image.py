"""
Tests the ASCII image support
"""

from . import vl
from ...imagestag import Colors
from ...imagestag.ascii_image import AsciiImage, AsciiImageMethod


def test_ascii_gray():
    image = vl.emoji("*globe*", return_image=True)
    color_img = AsciiImage(image=image, method=AsciiImageMethod.COLOR_ASCII)
    color_img.convert()
    color_img_g = AsciiImage(
        image=image.copy().convert("g"), method=AsciiImageMethod.COLOR_ASCII
    )
    color_img_g.convert()
    color_img_center = AsciiImage(
        image=image.copy().convert("rgb", bg_fill=Colors.BLACK),
        method=AsciiImageMethod.COLOR_ASCII,
        min_columns=30,
        max_columns=60,
        align="center",
    )
    color_img_center.convert()
    gray_image = AsciiImage(image=image, method=AsciiImageMethod.GRAY_LEVELS_69)
    gray_image.convert()
    gray_image_center = AsciiImage(
        image=image.copy().convert("g"),
        method=AsciiImageMethod.GRAY_LEVELS_69,
        max_columns=80,
        min_columns=120,
        align="right",
    )
    gray_image_center.convert()
    value = str(gray_image_center)
    assert len(value) == 4597
    vl.test.checkpoint("logging ascii")
    vl.log(color_img)
    vl.log(color_img_g)
    vl.log(color_img_center)
    vl.log(gray_image)
    vl.log(gray_image_center)
    vl.flush()
    vl.test.assert_cp_diff("0fd50af4f4e8a204660fd65752c2f98c")
