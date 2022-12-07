"""
Tests the Azure storage file sink
"""
import hashlib
import time

import pytest

from scistag.common import ConfigStag, SystemInfo
from scistag.filestag import FileSink, FileSource
from scistag.filestag.azure import AzureStorageFileSink
from scistag.webstag import web_fetch
from scistag.tests import RELEASE_TEST

sink_target_container_string = \
    "azure://DefaultEndpointsProtocol=https;AccountName=ikemscsteststorage;" \
    "AccountKey={{env.AZ_TEST_SOURCE_KEY}};EndpointSuffix=" \
    f"core.windows.net/testtarget{SystemInfo.os_type.identifier}"
"""
Test storage container
"""
sink_target_connection_string = \
    "azure://DefaultEndpointsProtocol=https;AccountName=ikemscsteststorage;" \
    "AccountKey={{env.AZ_TEST_SOURCE_KEY}};EndpointSuffix=" \
    "core.windows.net"
"Test connection string"

skip_tests = ConfigStag.get("testConfig.azure.skip", False)
"Defines if the Azure tests shall be skipped"

skip_long_tests = ConfigStag.get("testConfig.azure.skipLong", not RELEASE_TEST)
"Defines if the long running Azure tests shall be skipped"


@pytest.mark.skipif(skip_tests, reason="Azure tests disabled or not configured")
def test_azure_file_sink_basics():
    """
    Tests the Azure File sink basic functions. Uploads a file and verified
    if it can be downloaded again via an SAS Url.
    """
    sink = FileSink.with_target(sink_target_container_string)
    # store a very small file in the sink
    random_name = hashlib.md5(int(time.time()).to_bytes(16, "big")).hexdigest()
    verification_data = b"TestData" + random_name.encode("utf-8")
    sink.store(random_name, verification_data)
    download_url = sink.create_sas_url(random_name, end_time_days=1.0)
    assert len(download_url)
    test_data = web_fetch(download_url, max_cache_age=0)
    assert test_data == verification_data

    assert AzureStorageFileSink.setup_container(sink.service,
                                                "existing",
                                                create=True) is not None
    assert AzureStorageFileSink.setup_container(sink.service,
                                                "notexisting",
                                                create=False) is None
    assert AzureStorageFileSink.setup_container(sink.service,
                                                "existing",
                                                create=True,
                                                reuse_existing=False) is None


def test_azure_file_sink_creation():
    """
    Tests different creation variants
    """
    fs = AzureStorageFileSink(target=sink_target_container_string)
    assert fs.container is not None
    fs = AzureStorageFileSink(
        target=sink_target_container_string + "/subFolder")
    assert fs.sub_folder == "subFolder/"
    fs = AzureStorageFileSink(
        target=sink_target_container_string + "/subFolder2/")
    assert fs.sub_folder == "subFolder2/"
    fs = AzureStorageFileSink(
        target=sink_target_container_string)
    assert fs.sub_folder == ""
    fs = AzureStorageFileSink(
        target=sink_target_container_string, sub_folder="subFolder3")
    assert fs.sub_folder == "subFolder3/"
    with pytest.raises(ValueError):
        AzureStorageFileSink(target="nonsens")
    with pytest.raises(ValueError):
        AzureStorageFileSink(service="nonsens")
    with pytest.raises(ValueError):
        AzureStorageFileSink(service=None, target=None)
    fs = AzureStorageFileSink(service=sink_target_connection_string,
                              container="testcontainer")
    assert fs.container is not None
    fs = AzureStorageFileSink(service=sink_target_connection_string,
                              container="testcontainer",
                              create_container=False)
    assert fs.container is not None
    with pytest.raises(ValueError):
        fs = AzureStorageFileSink(service=sink_target_connection_string,
                                  container=None)
    with pytest.raises(ValueError):
        AzureStorageFileSink(service=sink_target_connection_string,
                             container=123)
    with pytest.raises(ValueError):
        AzureStorageFileSink(service=sink_target_connection_string,
                             container="notexistingcontainer",
                             create_container=False)


def test_azure_file_sink_upload():
    """
    Tests the AzureStorageFileSink upload functionality
    """
    full_target = sink_target_container_string

    with pytest.raises(ValueError):  # no filename
        AzureStorageFileSink.upload_file(full_target, data=b"123")
    assert AzureStorageFileSink.upload_file(full_target + "/testfiled.bin",
                                            data=b"123")
    with pytest.raises(ValueError):  # no container name
        AzureStorageFileSink.upload_file(sink_target_connection_string,
                                         data=b"123")
    with pytest.raises(ValueError):  # no data
        AzureStorageFileSink.upload_file(full_target + "/test.bin", data=None)
    with pytest.raises(ValueError):  # no url nor container nor service
        AzureStorageFileSink.upload_file("", data=b"123")
    assert AzureStorageFileSink.upload_file(
        service=sink_target_connection_string[8:],
        container="testcontainer",
        filename="testfile.bin", data=b"123")
    with pytest.raises(ValueError):  # no url nor container nor service
        assert AzureStorageFileSink.upload_file(
            service=sink_target_connection_string[8:],
            container="testcontainer",
            filename="testfile.bin", data=None)
    assert not AzureStorageFileSink.upload_file(
        service=sink_target_connection_string[8:],
        container="testcontainer",
        filename="testfile.bin", data=b"123", overwrite=False)
    with pytest.raises(ValueError):  # invalid container and not allowed to
        # create
        assert not AzureStorageFileSink.upload_file(
            service=sink_target_container_string,
            container="containerwhichcannotbecreated",
            filename="testfile.bin", data=b"123", overwrite=False,
            create_container=False)
    with pytest.raises(ValueError):  # invalid connection string
        assert not AzureStorageFileSink.upload_file(
            service=sink_target_container_string,
            container=None,
            filename="testfile.bin", data=b"123", overwrite=False)
    with pytest.raises(ValueError):  # invalid connection string
        assert not AzureStorageFileSink.upload_file(
            service="someInvalidString",
            container="testcontainer",
            filename="testfile.bin", data=b"123", overwrite=False)


@pytest.mark.skipif(skip_long_tests,
                    reason="Long running Azure tests disabled")
def test_azure_file_sink_deletion():
    """
    Tests recreation of containers
    """
    # ensure container exists
    AzureStorageFileSink(sink_target_container_string)
    AzureStorageFileSink(sink_target_container_string + "x")
    AzureStorageFileSink(sink_target_container_string + "empty")
    # test recreation
    with pytest.raises(ValueError):  # deletion requires some time
        AzureStorageFileSink(sink_target_container_string + "x",
                             recreate_container=True,
                             delete_timeout_s=0.1)
    sink = AzureStorageFileSink(sink_target_container_string)
    source = FileSource.from_source(sink_target_container_string + "empty",
                                    fetch_file_list=True)
    assert len(source.file_list) == 0
    # upload new data
    random_name = hashlib.md5(int(time.time()).to_bytes(16, "big")).hexdigest()
    verification_data = b"TestData" + random_name.encode("utf-8")
    sink.store(random_name, verification_data)
    time.sleep(1.0)
    source = FileSource.from_source(sink_target_container_string,
                                    fetch_file_list=True)
    assert len(source.file_list) >= 1
