"""
Tests the ImageBase class, the foundation of the :class:`Image` class
"""
from unittest import mock

import numpy as np
import pytest

from scistag.common.test_data import TestConstants
from scistag.imagestag import Image, PixelFormat
from scistag.imagestag.image_base import ImageBase


def test_normalize_to_gray():
    """
    Tests the gray normalization
    """
    org_image = image = Image(TestConstants.STAG_URL)
    image_rgba = org_image.copy().convert("rgba")
    image_cv = Image(TestConstants.STAG_URL, framework="CV")
    bgra_copy = Image(org_image.get_pixels(PixelFormat.BGRA))
    image_raw = Image(TestConstants.STAG_URL, framework="RAW")

    result_org = ImageBase.normalize_to_gray(image.pixels)
    result_org = ImageBase.normalize_to_gray(result_org)
    result_rgba = ImageBase.normalize_to_gray(image_rgba.pixels)
    result_cv = ImageBase.normalize_to_gray(
        image_cv.pixels, input_format=PixelFormat.BGR
    )
    result_cva = ImageBase.normalize_to_gray(
        bgra_copy.pixels, input_format=PixelFormat.BGRA
    )
    result_raw = ImageBase.normalize_to_gray(image_raw.pixels)
    assert np.all(result_org == result_cv)
    assert np.all(result_org == result_cva)
    assert np.all(result_org == result_raw)
    assert np.all(result_org == result_rgba)
    with mock.patch("scistag.imagestag.get_opencv", lambda: None):
        result_org = ImageBase.normalize_to_gray(image.pixels)
        result_rgba = ImageBase.normalize_to_gray(image_rgba.pixels)
        result_cv = ImageBase.normalize_to_gray(
            image_cv.pixels, input_format=PixelFormat.BGR
        )
        result_cva = ImageBase.normalize_to_gray(
            bgra_copy.pixels, input_format=PixelFormat.BGRA
        )
        result_raw = ImageBase.normalize_to_gray(image_raw.pixels)
        assert np.all(result_org == result_cv)
        assert np.all(result_org == result_cva)
        assert np.all(result_org == result_raw)
        assert np.all(result_org == result_rgba)
    img_cv2 = ImageBase.from_cv2(result_rgba)
    assert img_cv2.framework.name == "PIL"
    assert np.all(img_cv2.get_pixels_gray() == result_org)


def test_normalize_to_bgr():
    """
    Tests the bgr normalization
    """
    org_image = Image(TestConstants.STAG_URL)
    image = org_image.copy().convert("g")
    g_result = ImageBase.normalize_to_bgr(
        image.get_pixels_gray(), keep_gray=True, input_format=PixelFormat.GRAY
    )
    assert len(g_result.shape) == 2
    result = ImageBase.normalize_to_bgr(
        image.get_pixels_gray(), keep_gray=False, input_format=PixelFormat.GRAY
    )
    assert len(result.shape) == 3
    assert np.all(
        ImageBase.normalize_to_gray(result, input_format=PixelFormat.BGR) == g_result
    )


def test_normalize_to_rgb():
    """
    Tests the rgb normalization
    """
    org_image = Image(TestConstants.STAG_URL)
    image = org_image.copy().convert("g")
    g_result = ImageBase.normalize_to_rgb(
        image.get_pixels_gray(), keep_gray=True, input_format=PixelFormat.GRAY
    )
    assert len(g_result.shape) == 2
    result = ImageBase.normalize_to_rgb(
        image.get_pixels_gray(), keep_gray=False, input_format=PixelFormat.GRAY
    )
    assert len(result.shape) == 3
    result = ImageBase.normalize_to_rgb(
        org_image.get_pixels(), input_format=PixelFormat.RGB
    )
    assert len(result.shape) == 3
    assert np.all(result == org_image.get_pixels())


def test_bgr_to_rgb():
    """
    Tests RGB to BGR
    """
    org_image = Image(TestConstants.STAG_URL).convert("rgba")
    pixels = org_image.pixels
    bgr = ImageBase.bgr_to_rgb(pixels)
    assert np.any(pixels != bgr)
    assert np.all(ImageBase.bgr_to_rgb(bgr) == pixels)
    with pytest.raises(ValueError):
        ImageBase.bgr_to_rgb(org_image.get_pixels_gray())


def test_pixel_data_from_source():
    """
    Tests loading pixel data from a specific source
    """
    org_image = Image(TestConstants.STAG_URL).convert("rgba")
    pixels = org_image.pixels
    assert ImageBase._pixel_data_from_source(pixels) is pixels
    assert np.all(ImageBase._pixel_data_from_source(org_image.to_pil()) == pixels)
    with pytest.raises(NotImplementedError):
        assert ImageBase._pixel_data_from_source(123.45)
