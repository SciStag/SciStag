import pytest
from scistag.webstag import web_fetch
from scistag.tests import TestConstants


@pytest.fixture(scope="module")
def stag_image_data() -> bytes:
    """
    Returns the image data of a car
    :return: The jpeg data
    """
    yield web_fetch(TestConstants.STAG_URL, max_cache_age=60 * 60 * 48)
