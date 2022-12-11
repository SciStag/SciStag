"""
Implements the tests for the Emoji rendering
"""
import pytest

from . import vl
from ...emojistag import render_emoji, EmojiRenderer
from ...imagestag import Colors
from ...common.sytem_info import SystemInfo

SKIP_SVG = SystemInfo.os_type.is_windows and not EmojiRenderer.get_svg_support()


@pytest.mark.skipif(SKIP_SVG, reason="Svg tests skipped on Windows")
def test_rendering():
    """
    Tests the provision of pre-rendered PNGs
    """
    vl.test.begin("Rendering a simple emoji")
    vl.sub_test("The original emoji size is 136x128 pixels")
    emoji = render_emoji(":deer:")
    vl.test.assert_image(
        "emoji_original", source=emoji, hash_val="78b803a2a28c630c1eac8fabef4b78fb"
    )

    vl.sub_test("The emoji scaled by factor 2")
    emoji = render_emoji(":deer:", height=256)
    vl.test.assert_image(
        "emoji_original", source=emoji, hash_val="8c3ee19477710871fe24a1f0d8d950a0"
    )

    vl.sub_test("The emoji scaled by factor 2 in low quality")
    emoji = render_emoji(":deer:", height=256, quality=20)
    vl.test.assert_image(
        "emoji_original", source=emoji, hash_val="8311cdc4826c80d85fe6993b06adf9b6"
    )
    assert emoji.width == 272

    vl.sub_test("The emoji scaled by factor 0.5")
    emoji = render_emoji(":deer:", height=64)
    vl.test.assert_image(
        "emoji_original", source=emoji, hash_val="aed30f6809610e0f3c5378f2f53829d2"
    )
    assert emoji.width == 68
    vl.sub_test("The emoji scaled by factor 0.5 in high quality")
    emoji = render_emoji(":deer:", height=64, quality=100)
    vl.test.assert_image(
        "emoji_original", source=emoji, hash_val="2a70a627773654c67c97962536a51b3c"
    )

    vl.sub_test("The emoji scaled by factor 0.25")
    emoji = render_emoji(":deer:", height=32)
    vl.test.assert_image(
        "emoji_original", source=emoji, hash_val="0d4a0fb01037ce6d51f5e291e23f4180"
    )
    assert emoji.width == 34
    vl.sub_test("The emoji scaled by factor 0.25 in high quality")
    emoji = render_emoji(":deer:", height=32, quality=100)
    vl.test.assert_image(
        "emoji_original", source=emoji, hash_val="2615414b526ba8b09f852e7d36930af1"
    )


@pytest.mark.skipif(SKIP_SVG, reason="Svg tests skipped on Windows")
def test_emoji_background():
    """
    Tests rendering emojis w/ background
    """
    vl.test.begin("Emojis with background color (using PNGs)")
    vl.sub_test("Generating an emoji with black background")
    black_emoji = render_emoji(":sunglasses:", bg_color=Colors.BLACK)
    vl.test.assert_image(
        "black_background_emoji",
        black_emoji,
        hash_val="21ad9feeee35eba021c9eb6916c27075",
    )
    vl.sub_test("Generating an emoji with white background")
    white_emoji = render_emoji(":sunglasses:", bg_color=Colors.WHITE)
    vl.test.assert_image(
        "black_background_emoji",
        white_emoji,
        hash_val="ab9c2107eefbf527305ebb12d67af329",
    )

    vl.test.begin("Emojis with background color (using SVGs)")
    vl.sub_test("Generating an emoji with black background")
    black_emoji = render_emoji(":princess:", bg_color=Colors.BLACK, height=256)
    vl.test.assert_image(
        "black_background_emoji",
        black_emoji,
        hash_val="2813dd8f1a642188dea920ebc6ee735a",
    )
    vl.sub_test("Generating an emoji with white background")
    white_emoji = render_emoji(":princess:", bg_color=Colors.WHITE, height=256)
    vl.test.assert_image(
        "black_background_emoji",
        white_emoji,
        hash_val="984b8551d2def77519b01051acd41b0d",
    )
