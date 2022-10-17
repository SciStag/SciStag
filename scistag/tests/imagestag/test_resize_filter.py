import pytest

from scistag.imagestag import Color
from scistag.imagestag.filters import ResizeFilter
from scistag.tests.imagestag.image_tests_common import stag_image_data


def test_resize_filter(stag_image_data):
    """
    Tests the class ResizeFilter
    :param stag_image_data: The test image in bytes
    """
    # landscape
    resized_image = ResizeFilter(target_aspect=16 / 9).filter(stag_image_data)
    assert resized_image.width > resized_image.height
    resized_image_pixels = resized_image.get_pixels_bgr()
    mean = resized_image_pixels.mean()
    assert mean == pytest.approx(87.55, 0.01)
    # portrait
    resized_image = ResizeFilter(target_aspect=9 / 16, factor=2.0).filter(stag_image_data)
    resized_image_pixels = resized_image.get_pixels_bgr()
    mean = resized_image_pixels.mean()
    assert mean == pytest.approx(61.36, 0.01)
    assert resized_image.height > resized_image.width
    assert resized_image.width == 1330 and resized_image.height == 2102
    # portrait with red background
    resized_image = ResizeFilter(target_aspect=9 / 16, background_color=Color(1.0, 0.0, 0.0)).filter(stag_image_data)
    resized_image_pixels = resized_image.get_pixels_bgr()
    mean = resized_image_pixels.mean()
    assert mean == pytest.approx(101.80, 0.01)
    assert resized_image.height > resized_image.width
    # simple scaling
    resized_image = ResizeFilter(size=(500, 500)).filter(stag_image_data)
    resized_image_pixels = resized_image.get_pixels_bgr()
    mean = resized_image_pixels.mean()
    assert mean == pytest.approx(122.83, 0.01)
    assert resized_image.height == resized_image.width
    # factor only
    resized_image = ResizeFilter(factor=2.0).filter(stag_image_data)
    resized_image_pixels = resized_image.get_pixels_bgr()
    mean = resized_image_pixels.mean()
    assert mean == pytest.approx(122.85, 0.01)
    assert resized_image.width == 1330 and resized_image.height == 1050
    # fill image
    resized_image = ResizeFilter(size=(1000, 800), keep_aspect=True, fill_area=True).filter(stag_image_data)
    resized_image_pixels = resized_image.get_pixels_bgr()
    mean = resized_image_pixels.mean()
    assert mean == pytest.approx(122.85, 0.01)
    assert resized_image.width == 1000 and resized_image.height == 800
