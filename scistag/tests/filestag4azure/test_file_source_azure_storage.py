from __future__ import annotations

import os

import pytest

import scistag.tests
from scistag.common import ConfigStag
from scistag.filestag import FileSource
from scistag.filestag.azure.azure_blob_path import AzureBlobPath
from scistag.filestag.azure.azure_storage_file_source import \
    AzureStorageFileSource
from scistag.filestag.protocols import AZURE_PROTOCOL_HEADER
from scistag.webstag import web_fetch

ROBOTO_FONT_SIZE_WITHOUT_MD = 2043356
"The size of the fonts assumed on the server without the README"
TOTAL_FONT_COUNT = 20
"Total number of fonts in the repo"
ROBOTO_FONT_SIZE = 2054916
"The size of the fonts assumed on the server"
ROBOTO_FONT_COUNT = 13
"The number of fonts assumed on the server"

connection_string = \
    "azure://DefaultEndpointsProtocol=https;AccountName=ikemscsteststorage;" \
    "AccountKey={{env.AZ_TEST_SOURCE_KEY}};EndpointSuffix=" \
    "core.windows.net/testsource"
"""
Test storage
"""

test_source_sas_inv = os.environ["AZ_TEST_SOURCE_SAS_INV"]
"Test source using a SAS url"

test_source_sas = os.environ["AZ_TEST_SOURCE_SAS"]
"Test source using a SAS url"

skip_tests = ConfigStag.get("testConfig.azure.skip", False)
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
    assert azure_source.exists("Roboto/Roboto-Black.ttf")
    assert not azure_source.exists("Roboto/Roboto-BlackX2.ttf")

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


def test_no_recursion():
    """
    Tests that recursion can be suppressed
    """
    fs = FileSource.from_source(connection_string + "/data",
                                recursive=True)
    assert len(fs) == 4
    fs = FileSource.from_source(connection_string + "/data",
                                recursive=False)
    assert len(fs) == 0


def test_default_endpoint():
    """
    Tests that recursion can be suppressed
    """
    wo_azure = connection_string.lstrip("azure://") + "/fonts"
    fs = FileSource.from_source(wo_azure, recursive=True)
    assert len(fs) == 20


@pytest.mark.skipif(skip_tests, reason="Azure tests disabled or not configured")
def test_basics():
    """
    Provoke errors and edge cases
    """
    azure_source = FileSource.from_source(connection_string + "/fonts/Roboto")
    assert azure_source.fetch("notExistingFile.txt") is None
    assert azure_source.exists("LICENSE.txt")
    assert not azure_source.exists("WhatEver.zip")
    azure_source.close()
    azure_source.close()
    # don't list files, invalid files should not be provided though
    azure_source = FileSource.from_source(connection_string + "/fonts/Roboto",
                                          fetch_file_list=False)
    assert not azure_source.exists("LICENSE.md")
    azure_source.close()


@pytest.mark.skipif(skip_tests, reason="Azure tests disabled or not configured")
def test_tags():
    """
    Test the tag search functionality
    """
    azure_source = AzureStorageFileSource(connection_string,
                                          tag_filter="licenseFile = 'SciStag'",
                                          fetch_file_list=True)
    assert len(azure_source._file_list) == 1
    azure_source = AzureStorageFileSource(connection_string,
                                          tag_filter="licenseFile = 'SciStag'",
                                          fetch_file_list=False)
    file_count = 0
    for _ in azure_source:
        file_count += 1
    assert file_count == 1

    azure_source = AzureStorageFileSource(connection_string + "/fonts",
                                          tag_filter="licenseFile = 'Roboto'",
                                          fetch_file_list=True)
    assert len(azure_source._file_list) == 1
    # filter prefix and tag without prefetch
    azure_source = AzureStorageFileSource(connection_string + "/fonts",
                                          tag_filter="licenseFile = 'SciStag'",
                                          fetch_file_list=False)
    counter = 0
    for _ in azure_source:
        counter += 1
    assert counter == 0
    # filter prefix and tag without prefetch
    azure_source = AzureStorageFileSource(connection_string,
                                          tag_filter="licenseFile = 'SciStag'",
                                          fetch_file_list=False)
    counter = 0
    for _ in azure_source:
        counter += 1
    assert counter == 1


def test_tags_with_path():
    """
    Search for elements with tag in a search path
    """
    # filter prefix and tag with prefetch
    azure_source = AzureStorageFileSource(connection_string + "/fonts",
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
    full_url = f"{AZURE_PROTOCOL_HEADER}{conn_string}"
    elements = AzureBlobPath.split_azure_url(full_url)
    assert elements[0] == conn_string and elements[1] == "" and elements[
        2] == ""
    # connection string and container name
    container = "testData"
    full_url = f"{AZURE_PROTOCOL_HEADER}{conn_string}/{container}"
    elements = AzureBlobPath.split_azure_url(full_url)
    assert elements[0] == conn_string and elements[1] == container and elements[
        2] == ""
    # connection string and container name and unnecessary slash
    container = "testData"
    full_url = f"{AZURE_PROTOCOL_HEADER}{conn_string}/{container}/"
    elements = AzureBlobPath.split_azure_url(full_url)
    assert elements[0] == conn_string and elements[1] == container and elements[
        2] == ""
    prefix = "subPath"
    full_url = f"{AZURE_PROTOCOL_HEADER}{conn_string}/{container}/{prefix}"
    elements = AzureBlobPath.split_azure_url(full_url)
    assert elements[0] == conn_string and elements[1] == container and elements[
        2] == prefix
    # prefix and unnecessary slash
    full_url = f"{AZURE_PROTOCOL_HEADER}{conn_string}/{container}/{prefix}/"
    elements = AzureBlobPath.split_azure_url(full_url)
    assert elements[0] == conn_string and elements[1] == container and elements[
        2] == prefix
    # verify connection string parsing
    path = AzureBlobPath.from_string(conn_string)
    assert path.account_name == "123"
    assert path.account_key == "456"
    assert path.default_endpoints_protocol == "https"
    assert path.endpoint_suffix == "core.windows.net"


def test_sas_creation():
    """
    Tests the creation and usage of SAS tokens
    """

    azure_source: AzureStorageFileSource | None = FileSource.from_source(
        connection_string + "/fonts",
        fetch_file_list=True)
    assert len(azure_source._file_list) == TOTAL_FONT_COUNT
    assert azure_source.exists("Roboto/Roboto-Black.ttf")
    test_file = "Roboto/Roboto-Black.ttf"
    sas = azure_source.create_sas_url(test_file, end_time_days=1.0)
    assert len(sas)
    # read via sas url
    rest_data = web_fetch(sas, max_cache_age=0)
    # read via azure package
    blob_data = azure_source.fetch(test_file)
    # compare
    assert len(blob_data) == len(rest_data)
    assert blob_data == rest_data
    sas_data = web_fetch(
        azure_source.get_absolute("Roboto/Roboto-Black.ttf"))
    assert sas_data == blob_data


def test_sas_listing():
    """
    Tests the listing of a source using a SAS key
    """
    with pytest.raises(ValueError):
        source = FileSource.from_source(test_source_sas_inv)
    source = FileSource.from_source(test_source_sas,
                                    search_path="fonts")
    assert len(source.file_list) == 20
