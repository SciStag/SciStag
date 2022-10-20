import pytest

import scistag.tests
from scistag.common import ConfigStag
from scistag.filestag import FileSource
from scistag.filestag4azure.file_source_azure_storage import \
    FileSourceAzureStorage

ROBOTO_FONT_SIZE_WITHOUT_MD = 2043356
"The size of the fonts assumed on the server without the README"
TOTAL_FONT_COUNT = 20
"Total number of fonts in the repo"
ROBOTO_FONT_SIZE = 2054916
"The size of the fonts assumed on the server"
ROBOTO_FONT_COUNT = 13
"The number of fonts assumed on the server"

connection_string = ConfigStag.get(
    "testConfig.azure.storage.testSourceConnectionString")

skip_tests = ConfigStag.get("testConfig.azure.skip",
                            connection_string is None or
                            len(connection_string) == 0)
"Defines if the Azure tests shall be skipped"


@pytest.mark.skipif(skip_tests, reason="Azure tests disabled or not configured")
def test_iteration():
    """
    Tests general data iteration
    :return:
    """
    # test pre-fetch
    azure_source = FileSource.from_source(connection_string + "/fonts",
                                          fetch_file_list=True)
    assert len(azure_source._file_list) == TOTAL_FONT_COUNT
    assert azure_source.exists("fonts/Roboto/Roboto-Black.ttf")
    assert not azure_source.exists("fonts/Roboto/Roboto-BlackX2.ttf")

    # test dynamic iteration
    azure_source = FileSource.from_source(connection_string,
                                          fetch_file_list=False,
                                          max_file_count=30)
    count = 0
    size = 0
    for element in azure_source:
        count += 1
        size += len(element.data)
    assert count == 30


@pytest.mark.skipif(skip_tests, reason="Azure tests disabled or not configured")
def test_prefix():
    """
    Testing prefix filtering
    """
    azure_source = FileSource.from_source(connection_string + "/fonts/Roboto",
                                          fetch_file_list=True)
    assert len(azure_source._file_list) == ROBOTO_FONT_COUNT
    data_size = 0
    file_count = 0
    with FileSource.from_source(connection_string + "/fonts/Roboto",
                                search_mask="*.ttf") as font_source:
        for element in font_source:
            data_size += len(element.data)
            file_count += 1
    assert file_count == ROBOTO_FONT_COUNT - 1
    assert data_size == ROBOTO_FONT_SIZE_WITHOUT_MD


@pytest.mark.skipif(skip_tests, reason="Azure tests disabled or not configured")
def test_basics():
    """
    Provoke errors and edge cases
    """
    azure_source = FileSource.from_source(connection_string + "/fonts/Roboto")
    assert azure_source.read_file("notExistingFile.txt") is None
    assert azure_source.exists("scistag_essentials.zip")
    assert not azure_source.exists("WhatEver.zip")
    azure_source.close()
    azure_source.close()


@pytest.mark.skipif(skip_tests, reason="Azure tests disabled or not configured")
def test_tags():
    """
    Test the tag search functionality
    """
    azure_source = FileSourceAzureStorage(connection_string,
                                          tag_filter="licenseFile = 'SciStag'",
                                          fetch_file_list=True)
    assert len(azure_source._file_list) == 1
    azure_source = FileSourceAzureStorage(connection_string,
                                          tag_filter="licenseFile = 'SciStag'",
                                          fetch_file_list=False)
    file_count = 0
    for _ in azure_source:
        file_count += 1
    assert file_count == 1

    azure_source = FileSourceAzureStorage(connection_string + "/fonts",
                                          tag_filter="licenseFile = 'Roboto'",
                                          fetch_file_list=True)
    assert len(azure_source._file_list) == 1
    # filter prefix and tag without prefetch
    azure_source = FileSourceAzureStorage(connection_string + "/fonts",
                                          tag_filter="licenseFile = 'SciStag'",
                                          fetch_file_list=False)
    counter = 0
    for _ in azure_source:
        counter += 1
    assert counter == 0
    # filter prefix and tag without prefetch
    azure_source = FileSourceAzureStorage(connection_string,
                                          tag_filter="licenseFile = 'SciStag'",
                                          fetch_file_list=False)
    counter = 0
    for _ in azure_source:
        counter += 1
    assert counter == 1
    # filter prefix and tag with prefetch
    azure_source = FileSourceAzureStorage(connection_string + "/fonts",
                                          tag_filter="licenseFile = 'SciStag'",
                                          fetch_file_list=True)
    azure_source.handle_fetch_file_list()
    counter = 0
    for _ in azure_source:
        counter += 1
    assert counter == 0


@pytest.mark.skipif(skip_tests, reason="Azure tests disabled or not configured")
def test_conn_string():
    """
    Tests different elements of the connection string
    """
    # just connection string
    conn_string = \
        "DefaultEndpointsProtocol=https;AccountName=123;AccountKey=456;EndpointSuffix=core.windows.net"
    full_url = f"azure://{conn_string}"
    elements = FileSourceAzureStorage.split_azure_url(full_url)
    assert elements[0] == conn_string and elements[1] == "" and elements[
        2] == ""
    # connection string and container name
    container = "testData"
    full_url = f"azure://{conn_string}/{container}"
    elements = FileSourceAzureStorage.split_azure_url(full_url)
    assert elements[0] == conn_string and elements[1] == container and elements[
        2] == ""
    # connection string and container name and unnecessary slash
    container = "testData"
    full_url = f"azure://{conn_string}/{container}/"
    elements = FileSourceAzureStorage.split_azure_url(full_url)
    assert elements[0] == conn_string and elements[1] == container and elements[
        2] == ""
    prefix = "subPath"
    full_url = f"azure://{conn_string}/{container}/{prefix}"
    elements = FileSourceAzureStorage.split_azure_url(full_url)
    assert elements[0] == conn_string and elements[1] == container and elements[
        2] == prefix
    # prefix and unnecessary slash
    full_url = f"azure://{conn_string}/{container}/{prefix}/"
    elements = FileSourceAzureStorage.split_azure_url(full_url)
    assert elements[0] == conn_string and elements[1] == container and elements[
        2] == prefix
    elements = FileSourceAzureStorage.split_azure_url(conn_string)
    assert elements is None
