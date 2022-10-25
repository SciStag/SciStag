"""
Implements the tests for the :class:`FileSourceZip`.
"""

import pytest

from scistag.common.essential_data import get_edp, ESSENTIAL_DATA_ARCHIVE_NAME
from scistag.filestag import FileSource, FileStag

TEST_PNG_TOTAL_SIZE = 10297508
"Total size of all PNGs"

TEST_PNG_COUNT = 3680
"Total PNG count"

TEST_ARCHIVE_EXTRACTED_FILE_SIZE = 17074382
"Total data size in our essential data archive"

TEST_ARCHIVE_FILE_COUNT = 3706
"Count of files in our zip file"


def test_zip_source_prefetched():
    """
    Test general functionality with pre-fetched file list
    """
    get_edp()  # guarantee availability of essential data zip
    with FileSource.from_source(ESSENTIAL_DATA_ARCHIVE_NAME, fetch_file_list=True) as test_source:
        test_source.handle_fetch_file_list()  # as a test
        assert len(test_source._file_list) == TEST_ARCHIVE_FILE_COUNT
        assert test_source.exists("README.md")
        assert not test_source.exists("READMExr.md")
        files_handled = 0
        total_data = 0
        for element in test_source:
            files_handled += 1
            total_data += len(element.data)
        assert files_handled == TEST_ARCHIVE_FILE_COUNT
        assert total_data == TEST_ARCHIVE_EXTRACTED_FILE_SIZE
        with pytest.raises(FileNotFoundError):
            test_source.read_file("doesnexist.txt")


def test_zip_source_dynamic():
    """
    Test directly iterating all files without pre-fetch
    """
    with FileSource.from_source(ESSENTIAL_DATA_ARCHIVE_NAME) as test_source:
        assert test_source._file_list is None

        assert test_source.exists("README.md")
        assert not test_source.exists("READMExr.md")

        files_handled = 0
        total_data = 0
        for element in test_source:
            files_handled += 1
            total_data += len(element.data)
        assert files_handled == TEST_ARCHIVE_FILE_COUNT
        assert total_data == TEST_ARCHIVE_EXTRACTED_FILE_SIZE


def test_zip_in_memory():
    """
    Test using a memory zip
    """
    zip_data = FileStag.load(ESSENTIAL_DATA_ARCHIVE_NAME)
    with FileSource.from_source(zip_data) as test_source:
        assert test_source._file_list is None

        assert test_source.exists("README.md")
        assert not test_source.exists("READMExr.md")

        files_handled = 0
        total_data = 0
        for element in test_source:
            files_handled += 1
            total_data += len(element.data)
        assert files_handled == TEST_ARCHIVE_FILE_COUNT
        assert total_data == TEST_ARCHIVE_EXTRACTED_FILE_SIZE
    test_source.close()  # close twice


def test_dynamic_filtering():
    """
    Test using a memory zip
    """
    zip_data = FileStag.load(ESSENTIAL_DATA_ARCHIVE_NAME)
    with FileSource.from_source(zip_data, search_mask="*.png") as test_source:
        assert test_source._file_list is None
        files_handled = 0
        total_data = 0
        for element in test_source:
            files_handled += 1
            total_data += len(element.data)
        assert files_handled == TEST_PNG_COUNT
        assert total_data == TEST_PNG_TOTAL_SIZE
    test_source.close()  # close twice


def test_zip_source_filtering():
    """
    Test basic filtering
    """
    with FileSource.from_source(ESSENTIAL_DATA_ARCHIVE_NAME, fetch_file_list=True, recursive=False) as test_source:
        assert len(test_source._file_list) == 2


def test_file_stag_protocol():
    """
    Tests if files can also be loaded via the FileStag protocol, e.g. a zip in a zip
    """
    with FileSource.from_source("file://" + ESSENTIAL_DATA_ARCHIVE_NAME, fetch_file_list=True) as test_source:
        assert len(test_source._file_list) == TEST_ARCHIVE_FILE_COUNT
