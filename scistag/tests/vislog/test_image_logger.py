"""
Tests the ImageLogger
"""

import pytest

from ...common.test_data import TestConstants
from ...emojistag import render_emoji
from ...imagestag import Colors
from ...vislog import VisualLog
from . import vl
from ...vislog.options import LogOptions


def test_image():
    """
    Tests image logging
    """
    image_data = render_emoji(":deer:")
    image_data.convert("rgb", bg_fill=Colors.WHITE)
    # logging images
    vl.test.assert_image(
        "stag",
        source=image_data,
        alt="An image of a stag - just because we can",
        hash_val="4e5e428357fcf315f25b148747d633db",
        scaling=0.5,
    )
    vl.test.checkpoint("image.log.disabled")
    vl.options.style.image.log_images = False
    vl.image(image_data, alt="an image which shouldn't get logged")
    vl.options.style.image.log_images = True
    vl.test.assert_cp_diff("d41d8cd98f00b204e9800998ecf8427e")
    # insert image via canvas
    vl.image(source=image_data.to_canvas(), name="stag_canvas")
    # insert image via pixel data
    vl.image(source=image_data.get_pixels(), name="stag_canvas_2")
    # insert image via pixel data scaled
    vl.image(source=image_data.encode("jpg"), name="stag_canvas_2", scaling=0.7)
    # insert image scaled with maximum width
    vl.image(source=image_data.get_pixels(), name="stag_canvas_2", max_width=200)
    with pytest.raises(ValueError):
        # insert image scaled
        vl.image(
            source=image_data.get_pixels(),
            name="stag_canvas_2",
            max_width=200,
            scaling=0.5,
        )
    with pytest.raises(ValueError):
        # insert image scaled (float)
        vl.image(source=image_data.get_pixels(), name="stag_canvas_2", max_width=199.8)
    # insert image scaled (float)
    vl.image(source=image_data.get_pixels(), name="stag_canvas_2", max_width=0.5)
    # test using general assert
    vl.test.assert_val(
        "assert_stag", image_data, hash_val="4e5e428357fcf315f25b148747d633db"
    )
    with pytest.raises(AssertionError):
        vl.test.assert_val("assert_stag", image_data, hash_val="124567")
    vl.test.checkpoint("image.log.scaled.nodownload")
    vl.sub_test("An image from the web scaled to 50%")
    vl.image(TestConstants.STAG_URL, "anotherStag_1", scaling=0.5, download=False)
    vl.test.assert_cp_diff(hash_val="28b1f6534b36b20b083ece585b93ec1b")
    vl.test.checkpoint("image.log.scaled.downloaded")
    vl.sub_test("An image from the web scaled to 50% w/ downloading")
    vl.image(TestConstants.STAG_URL, "anotherStag_2", scaling=0.5, download=True)
    vl.test.checkpoint("image.log.originalSize")
    vl.sub_test("An image from the web scaled to 100%")
    vl.image(TestConstants.STAG_URL, "anotherStag_3", scaling=1.0)
    vl.test.assert_cp_diff(hash_val="a490b9c1634df6b0d24c801e89ebbcd0")
    # add image from bytes stream
    vl.sub_test("Logging an image provided as byte stream")
    vl.test.checkpoint("image.log.bytestream")
    vl.image(image_data.encode(), alt="image from byte stream")
    vl.add(image_data.encode())
    # insert image from web (as url)
    vl.image(
        TestConstants.STAG_URL,
        alt="Image link from URL",
        download=False,
        scaling=0.5,
    )
    # insert image from web (inserted)
    vl.image(
        TestConstants.STAG_URL,
        alt="Image download from URL",
        download=True,
        scaling=0.5,
    )
    vl.test.begin("image.logviaadd")
    vl.add(image_data)
    # testing file type
    vl.image(source=image_data, filetype="jpg")
    # testing file type
    vl.image(source=image_data, filetype=("jpg", 70))
    # testing scaled image reference
    vl.image(TestConstants.STAG_URL, "anotherStag_1", max_width=128)
    # testing scaled image reference
    vl.image(TestConstants.STAG_URL, "anotherStag_1", max_width=0.5)
    with pytest.raises(ValueError):
        # testing scaled image reference
        vl.image(TestConstants.STAG_URL, "anotherStag_1", max_width=100.0)

    out_log = VisualLog().default_builder
    out_log.options.style.image.embed_images = False
    out_log.image(source=image_data, filetype="jpg")
    # testing file type
