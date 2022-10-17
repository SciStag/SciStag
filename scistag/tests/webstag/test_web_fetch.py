"""
Tests the functionality of the web_fetch method and the WebCache class
"""
import os
import time
import uuid

import pytest

from scistag.common.test_data import TestConstants
from scistag.webstag.web_fetch import web_fetch, FROM_CACHE, STORED_IN_CACHE, \
    WebCache
from . import skip_webstag

URL = TestConstants.STAG_URL
"""
The SciStag homepage
"""

INVALID_URL = "https://scistag.org/12345"
"""
An invalid URL
"""


@pytest.mark.skipif(skip_webstag, reason="Web tests disabled or not configured")
def test_web_fetch_and_cache(tmp_path):
    """
    Tests the web_fetch method
    """
    homepage = web_fetch(URL, max_cache_age=0.5)
    assert homepage is not None and len(homepage) > 0
    # Verify data is in the cache now
    assert WebCache.find(URL) is not None
    # Verify data is not in the cache
    assert WebCache.find(INVALID_URL) is None
    response_details = {}
    web_fetch(URL, max_cache_age=0.5, out_response_details=response_details)
    WebCache.cleanup()
    assert response_details.get(FROM_CACHE, False)  # should still be in cache
    assert not response_details.get(STORED_IN_CACHE,
                                    False)  # should still be in cache
    time.sleep(0.6)
    # trigger deletion of old variant
    response_details = {}
    stag_data = web_fetch(URL, max_cache_age=0.5,
                          out_response_details=response_details)
    WebCache.cleanup()
    assert not response_details.get(FROM_CACHE,
                                    False)  # should have been removed by now due to timeout
    assert response_details.get(STORED_IN_CACHE,
                                False)  # should still be in cache
    WebCache.flush()
    # store on disk
    out_filename = str(tmp_path) + f"/stag_{uuid.uuid4()}.png"
    web_fetch(URL, filename=out_filename)
    assert os.path.exists(out_filename)
    assert os.path.getsize(out_filename) == len(stag_data)
