"""
Tests the Azure storage file sink
"""
import hashlib
import time

import pytest

from scistag.common import ConfigStag
from scistag.filestag import FileSink, FileSource
from scistag.filestag.azure import AzureStorageFileSink
from scistag.webstag import web_fetch

sink_target_connection_string = \
    "azure://DefaultEndpointsProtocol=https;AccountName=ikemscsteststorage;" \
    "AccountKey={{env.AZ_TEST_SOURCE_KEY}};EndpointSuffix=" \
    "core.windows.net/testtarget"
"""
Test storage
"""

skip_tests = ConfigStag.get("testConfig.azure.skip", False)
"Defines if the Azure tests shall be skipped"

skip_long_tests = ConfigStag.get("testConfig.azure.skipLong", False)
"Defines if the long running Azure tests shall be skipped"


@pytest.mark.skipif(skip_tests, reason="Azure tests disabled or not configured")
def test_azure_file_sink_basics():
    """
    Tests the Azure File sink basic functions. Uploads a file and verified
    if it can be downloaded again via an SAS Url.
    """
    sink = FileSink.with_target(sink_target_connection_string)
    # store a very small file in the sink
    random_name = hashlib.md5(int(time.time()).to_bytes(16, "big")).hexdigest()
    verification_data = b"TestData" + random_name.encode("utf-8")
    sink.store(random_name, verification_data)
    download_url = sink.create_sas_url(random_name, end_time_days=1.0)
    assert len(download_url)
    test_data = web_fetch(download_url, max_cache_age=0)
    assert test_data == verification_data


@pytest.mark.skipif(skip_long_tests,
                    reason="Long running Azure tests disabled")
def test_azure_file_sink_deletion():
    """
    Tests recreation of containers
    """
    # ensure container exists
    AzureStorageFileSink(sink_target_connection_string)
    # test recreation
    with pytest.raises(ValueError):  # deletion requires some time
        AzureStorageFileSink(sink_target_connection_string,
                             recreate_container=True,
                             delete_timeout_s=0.5)
    sink = AzureStorageFileSink(sink_target_connection_string,
                                recreate_container=True)
    source = FileSource.from_source(sink_target_connection_string,
                                    fetch_file_list=True)
    assert len(source.get_file_list()) == 0
    # upload new data
    random_name = hashlib.md5(int(time.time()).to_bytes(16, "big")).hexdigest()
    verification_data = b"TestData" + random_name.encode("utf-8")
    sink.store(random_name, verification_data)
    time.sleep(1.0)
    source = FileSource.from_source(sink_target_connection_string,
                                    fetch_file_list=True)
    assert len(source.get_file_list()) == 1
