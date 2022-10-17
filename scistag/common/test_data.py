"""
Provides test data
"""

from __future__ import annotations
import tempfile
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from scistag.imagestag import Image


class TestConstants:
    """
    Definition of shared testing resource locations and constants
    """

    STAG_URL = "https://github.com/SciStag/SciStagEssentialData/releases/download/v0.0.2/stag.jpg"
    STAG_IMAGE_SIZE = 67104

    CHROME_FUN_VIDEO = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"


class TestDataNames:
    """
    Definition of test data names
    """

    STAG = "stag"
    "The photo of a stag in the forest"


TEST_DATA_URLS = {TestDataNames.STAG: TestConstants.STAG_URL}
"List of URLs providing test data"

TEST_DATA_CACHE_AGE = 30 * 24 * 60 * 60
"""
Keep test data for one month
"""


def get_test_data(name: str) -> bytes | None:
    """
    Returns test data with the specified name. See :const:`TEST_DATA_URLS`

    :param name: The data name, e.g. stag
    :return: The data
    """
    if name not in TEST_DATA_URLS:
        return None
    from scistag.webstag import web_fetch
    data = web_fetch(TEST_DATA_URLS[name],
                     max_cache_age=TEST_DATA_CACHE_AGE)
    return data


def get_test_image(name: str) -> Union["Image", None]:
    """
    Returns a test image with given name.

    See :const:`TEST_DATA_URLS`.

    :param name: The name of the example image to fetch
    :return: The image
    """
    from scistag.imagestag import Image
    test_data = get_test_data(name)
    if test_data is None:
        return None
    image = Image(test_data)
    return image
