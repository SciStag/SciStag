"""
Tests the VisualImageLogger
"""

import pytest

from ...common.test_data import TestConstants
from ...emojistag import render_emoji
from ...imagestag import Colors
from . import vl


def test_image():
    """
    Tests image logging
    """
    image_data = render_emoji(":deer:")
    image_data.convert("rgb", bg_fill=Colors.WHITE)
    # logging images
    vl.test.assert_image("stag",
                         source=image_data,
                         alt_text="An image of a stag - just because we can",
                         hash_val='4e5e428357fcf315f25b148747d633db',
                         scaling=0.5)
    vl.test.checkpoint("image.log.disabled")
    vl.target_log.log_images = False
    vl.image(image_data, alt_text="an image which shouldn't get logged")
    vl.target_log.log_images = True
    vl.test.assert_cp_diff("d41d8cd98f00b204e9800998ecf8427e")
    # insert image via canvas
    vl.image(source=image_data.to_canvas(), name="stag_canvas")
    # insert image via pixel data
    vl.image(source=image_data.get_pixels(), name="stag_canvas_2")
    # test using general assert
    vl.test.assert_val("assert_stag", image_data,
                       hash_val='4e5e428357fcf315f25b148747d633db')
    with pytest.raises(AssertionError):
        vl.test.assert_val("assert_stag", image_data,
                           hash_val='4e5e428357fcf315f25b148747d633da')
    vl.test.checkpoint("image.log.scaled.nodownload")
    vl.log_txt_images = False
    vl.sub_test("An image from the web scaled to 50%")
    vl.image(TestConstants.STAG_URL, "anotherStag_1", scaling=0.5,
             download=False)
    vl.test.assert_cp_diff(hash_val="c9aa5a4232351b81ec4b8607126c0dd0")
    vl.test.checkpoint("image.log.scaled.downloaded")
    vl.sub_test("An image from the web scaled to 50% w/ downloading")
    vl.image(TestConstants.STAG_URL, "anotherStag_2", scaling=0.5,
             download=True)
    vl.test.checkpoint("image.log.originalSize")
    vl.sub_test("An image from the web scaled to 100%")
    vl.image(TestConstants.STAG_URL, "anotherStag_3", scaling=1.0)
    vl.log_txt_images = True
    vl.test.assert_cp_diff(hash_val="a37201edd6c4c71f056f0a559ad6824b")
    # add image from bytes stream
    vl.sub_test("Logging an image provided as byte stream")
    vl.test.checkpoint("image.log.bytestream")
    vl.image(image_data.encode(), alt_text="image from byte stream")
    # insert image from web (as url)
    vl.image(TestConstants.STAG_URL, alt_text="Image link from URL",
             download=False,
             scaling=0.5)
    # insert image from web (inserted)
    vl.image(TestConstants.STAG_URL, alt_text="Image download from URL",
             download=True,
             scaling=0.5)
    vl.test.begin("image.logviaadd")
    vl.add(image_data)
