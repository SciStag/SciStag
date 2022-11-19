"""
Tests the FileStag class
"""
import os.path
import shutil

import pytest
from pydantic import SecretStr

from scistag.filestag import FileStag, ZIP_SOURCE_PROTOCOL
from scistag.common.test_data import TestConstants
from scistag.common.essential_data import ESSENTIAL_DATA_ARCHIVE_NAME, get_edp

get_edp()


def test_file_stag():
    """
    Test the base functionality of the FileStag class
    """
    # load file from disk
    ed = FileStag.load(ESSENTIAL_DATA_ARCHIVE_NAME)
    assert FileStag.load(ESSENTIAL_DATA_ARCHIVE_NAME + "123") is None
    assert len(ed) == 13754681
    # load file from the web
    stag_image = FileStag.load(TestConstants.STAG_URL, cache=True)
    stag_image = FileStag.load(SecretStr(TestConstants.STAG_URL), cache=True)
    assert len(stag_image) == 308019
    # load file directly from archive
    readme = FileStag.load(ZIP_SOURCE_PROTOCOL +
                           ESSENTIAL_DATA_ARCHIVE_NAME + "/README.md")
    assert len(readme) == 2234
    edp = get_edp()
    mdi = FileStag.load(
        edp + "/data/material_design/material_design_icon_names.json")
    assert len(mdi) == 227233
    # exists
    assert FileStag.exists(ESSENTIAL_DATA_ARCHIVE_NAME)
    assert FileStag.exists(SecretStr(ESSENTIAL_DATA_ARCHIVE_NAME))
    assert FileStag.exists("file://" + ESSENTIAL_DATA_ARCHIVE_NAME)
    assert not FileStag.load(ESSENTIAL_DATA_ARCHIVE_NAME + "nonsense")
    assert FileStag.exists(
        ZIP_SOURCE_PROTOCOL + ESSENTIAL_DATA_ARCHIVE_NAME + "/README.md")
    assert not FileStag.exists(
        ZIP_SOURCE_PROTOCOL + ESSENTIAL_DATA_ARCHIVE_NAME + "/READMExk.md")
    assert FileStag.exists(TestConstants.STAG_URL, cache=True)
    assert not FileStag.exists(TestConstants.STAG_URL + "nonsense")
    assert not FileStag.delete("notexisting123")
    with pytest.raises(NotImplementedError):
        FileStag.delete("https://www.google.com")
    with pytest.raises(NotImplementedError):
        FileStag.save("https://www.google.com", b"yahoo")
    assert not FileStag.save("/somenotexistingfolder/youcantaccess", b"yahoo")


def test_simple_file():
    """
    Tests the "is_simple_file_ function for different types
    """
    assert FileStag.is_simple(ESSENTIAL_DATA_ARCHIVE_NAME)
    assert FileStag.is_simple(SecretStr(ESSENTIAL_DATA_ARCHIVE_NAME))
    assert not FileStag.is_simple(TestConstants.STAG_URL)
    assert not FileStag.is_simple(
        ZIP_SOURCE_PROTOCOL + ESSENTIAL_DATA_ARCHIVE_NAME + "/README.md")


def test_json(tmp_path):
    """
    Test JSON saving and loading
    """
    some_dict = {"name": "Michael", "size": 1.82}
    output_fn = str(tmp_path) + '/fstest.json'
    FileStag.delete(output_fn)
    FileStag.save_json(output_fn, some_dict)
    loaded_dict = FileStag.load_json(output_fn)
    assert FileStag.load_json(output_fn + "123") is None
    assert some_dict == loaded_dict
    assert FileStag.delete(SecretStr(output_fn))
    FileStag.save_json(SecretStr(output_fn), some_dict)
    loaded_dict = FileStag.load_json(SecretStr(output_fn))
    assert some_dict == loaded_dict


def test_text(tmp_path):
    """
    Tests storing and loading text
    """
    output_fn = str(tmp_path) + '/fstest.text'
    test_data = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, " \
                "sed \n" \
                "do eiusmod tempor incididunt ut labore et dolore \n" \
                "magna aliqua. Ut enim ad"
    FileStag.save_text(output_fn, test_data)
    assert FileStag.load_text(output_fn) == test_data
    assert FileStag.load_text(output_fn + "123") is None
    assert FileStag.delete(output_fn)
    FileStag.save_text(SecretStr(output_fn), test_data)
    assert os.path.exists(output_fn)
    assert FileStag.load_text(SecretStr(output_fn)) == test_data
    assert FileStag.delete(SecretStr(output_fn))


def test_copy(tmp_path):
    """
    Tests FileStag's copy functionality
    """
    output_fn = str(tmp_path) + '/fstest.text'
    test_data = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, " \
                "sed \n" \
                "do eiusmod tempor incididunt ut labore et dolore \n" \
                "magna aliqua. Ut enim ad"
    FileStag.save_text(output_fn, test_data)
    sub_folder = str(tmp_path) + "/subfolder"
    if os.path.exists(sub_folder):
        shutil.rmtree(sub_folder)
    assert not FileStag.copy(output_fn, sub_folder + "/copy.txt",
                             create_dir=False)
    assert FileStag.copy(output_fn, sub_folder + "/copy.txt",
                         create_dir=True)
    assert os.path.exists(sub_folder + "/copy.txt")
    FileStag.copy(SecretStr(output_fn), SecretStr(sub_folder + "/copy2.txt"))
    assert not FileStag.copy("/fqw32323/2323213",
                             SecretStr(sub_folder + "/copy2.txt"))
    assert os.path.exists(sub_folder + "/copy2.txt")
    FileStag.copy(SecretStr(TestConstants.STAG_URL),
                  SecretStr(sub_folder + "/stag.jpg"))
    assert os.path.getsize(sub_folder + "/stag.jpg") == 308019
