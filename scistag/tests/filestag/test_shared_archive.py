"""
Tests the functionality of the SharedArchive class
"""
import pytest

from scistag.common.essential_data import get_edp, ESSENTIAL_DATA_ARCHIVE_NAME
from scistag.filestag import FileStag, SharedArchive, ZIP_SOURCE_PROTOCOL
from scistag.addons import AddonManager

edp = get_edp()


def test_scan():
    """
    Tests the base functionality of the SharedArchive class
    """
    assert len(edp)
    assert SharedArchive.is_loaded(ESSENTIAL_DATA_ARCHIVE_NAME)
    assert not SharedArchive.is_loaded(ESSENTIAL_DATA_ARCHIVE_NAME + "NonSense")
    addon_paths = AddonManager.get_addons_paths("emojis.*")
    assert "emojis.svg" in addon_paths


def test_exists():
    """
    Tests file existence
    """
    addon_paths = AddonManager.get_addons_paths("emojis.*")
    svg_path = addon_paths["emojis.svg"]
    # scan
    svg_files = SharedArchive.scan(svg_path, name_filter="*.svg", long_identifier=False)
    assert len(svg_files) > 0
    assert not svg_files[0].startswith(ZIP_SOURCE_PROTOCOL)
    svg_files = SharedArchive.scan(svg_path, name_filter="*.svg", long_identifier=True)
    assert len(svg_files) > 0
    assert svg_files[0].startswith(ZIP_SOURCE_PROTOCOL)
    assert SharedArchive.scan("NotExisting", name_filter="*.svg", long_identifier=True) == []
    # verify file
    assert SharedArchive.exists_at_source(svg_files[0])
    assert not SharedArchive.exists_at_source(svg_files[0] + "/someNonsense")
    fake_name = ZIP_SOURCE_PROTOCOL + "@doesNotExist/someFile.txt"
    assert not SharedArchive.exists_at_source(fake_name)

    svg_file_data = SharedArchive.load_file(svg_files[0])
    assert len(svg_file_data) == 13094
    svg_file_data = SharedArchive.load_file(svg_files[0] + "_not_existing")
    assert svg_file_data is None


def test_register_and_unload():
    """
    Tests the registration and unregistration of archives
    """
    assert SharedArchive.load_file("NotExisting") is None

    data = FileStag.load_file(ESSENTIAL_DATA_ARCHIVE_NAME)
    # test if archive is not registered twice
    prev_count = len(SharedArchive.archives)
    SharedArchive.register(ESSENTIAL_DATA_ARCHIVE_NAME, "scistagessential")
    assert len(SharedArchive.archives) == prev_count
    # load from bytes using another identifier
    SharedArchive.register(data, "TempEssentialData")
    assert len(SharedArchive.archives) == prev_count + 1
    # load from file and using caching
    SharedArchive.register(ESSENTIAL_DATA_ARCHIVE_NAME, "TempEssentialData2", cache=True)
    assert len(SharedArchive.archives) == prev_count + 2
    assert SharedArchive.unload(identifier="TempEssentialData")
    assert SharedArchive.unload(identifier="TempEssentialData2")
    assert not SharedArchive.unload(identifier="NotExisting")


def test_url_verification():
    """
    Tests the split function
    """
    with pytest.raises(ValueError):
        SharedArchive._split_identifier_and_filename(ZIP_SOURCE_PROTOCOL + "someFile.zip")
    with pytest.raises(ValueError):
        SharedArchive._split_identifier_and_filename(ZIP_SOURCE_PROTOCOL + "@someFile")
