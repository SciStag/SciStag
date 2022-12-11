import pytest

from scistag.imagestag.filters import ImageFilterSeries, CropFilter
from scistag.imagestag.filters.color_map_filter import (
    ColorMapFilter,
    COLOR_MAP_VIRIDIS,
    COLOR_MAP_INFERNO,
)
from .image_tests_common import stag_image_data
from . import skip_imagestag


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_colormap_filter(stag_image_data):
    """
    Tests the class ColorMapFilter
    :param stag_image_data: The test image as byte data
    """
    result_image = ColorMapFilter(color_map=COLOR_MAP_VIRIDIS, normalize=False).filter(
        stag_image_data
    )
    pixel_data = result_image.get_pixels_bgr()
    mean = pixel_data.mean()
    assert mean == pytest.approx(108.02, 0.01)
    assert result_image.width == 665 and result_image.height == 525
    series = ImageFilterSeries(
        filters=[
            CropFilter(box=(150, 100, 350, 300)),
            ColorMapFilter(color_map=COLOR_MAP_VIRIDIS, normalize=True),
        ]
    )
    result_image = series.filter(stag_image_data)
    pixel_data = result_image.get_pixels_bgr()
    mean = pixel_data.mean()
    assert mean == pytest.approx(104.052, 0.01)
    assert result_image.width == 200 and result_image.height == 200
    result_image = ColorMapFilter(color_map=COLOR_MAP_INFERNO, normalize=False).filter(
        stag_image_data
    )
    pixel_data = result_image.get_pixels_bgr()
    mean = pixel_data.mean()
    assert mean == pytest.approx(104.09, 0.01)
    assert result_image.width == 665 and result_image.height == 525
