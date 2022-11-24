"""
Tests the :class:`FileSource` class.

With the :class:`FileSource` class you can iterate through directories, archives or cloud storage sources
file by file with a minimum of code.
"""
import os.path
import shutil

import pytest
from pydantic import SecretStr

from scistag.filestag import FileSource, FileStag, FilePath

from . import vl
from ...common import ESSENTIAL_DATA_ARCHIVE_NAME


def test_scan():
    """
    Tests the basic scanning functionality
    """
    base_dir = os.path.normpath(os.path.dirname(__file__) + "/..")

    source = FileSource.from_source(base_dir, recursive=False,
                                    fetch_file_list=True)
    assert len(source._file_list) >= 1
    assert len(source._file_list) < 10

    source = FileSource.from_source(base_dir, recursive=True,
                                    fetch_file_list=True)
    assert len(source._file_list) >= 150
    assert len(source._file_list) < 550


def test_iteration():
    """
    Tests the iteration through a list of files
    """
    base_dir = os.path.normpath(os.path.dirname(__file__) + "/../filestag")
    source = FileSource.from_source(base_dir, recursive=True,
                                    fetch_file_list=True, search_mask="*.py")
    assert len(source._file_list) >= 3
    assert len(source._file_list) < 10

    total_size = 0
    total_count = 0
    for element in source:
        total_count += 1
        total_size += len(element.data)

    assert 3 <= total_count <= 10
    assert total_size >= 5000


def test_sharing():
    """
    Tests sharing a task between multiple helpers
    """
    helper_count = 3

    base_dir = os.path.normpath(os.path.dirname(__file__) + "/..")
    full_list = FileSource.from_source(base_dir, fetch_file_list=True,
                                       search_mask="*.py")._file_list
    full_set = set([element.filename for element in full_list])

    prior_set = set()
    # verify file list pre-fetch with skip
    for sub_index in range(helper_count):
        part_list = FileSource.from_source(base_dir, fetch_file_list=True,
                                           index_filter=(
                                               helper_count, sub_index),
                                           search_mask="*.py").reduce_file_list()
        cur_set = set([element.filename for element in part_list])
        assert len(cur_set) > 0
        assert len(prior_set.intersection(cur_set)) == 0
        prior_set = prior_set.union(cur_set)
        assert len(prior_set.intersection(cur_set)) >= 1

    assert len(full_set.intersection(prior_set)) == len(full_set)
    # verify iteration with skip
    prior_set = set()
    for sub_index in range(helper_count):
        source = FileSource.from_source(base_dir,
                                        index_filter=(helper_count, sub_index),
                                        search_mask="*.py")
        cur_set = set()
        for element in source:
            cur_set.add(element.filename)
        assert len(cur_set) > 0
        assert len(prior_set.intersection(cur_set)) == 0
        prior_set = prior_set.union(cur_set)
        assert len(prior_set.intersection(cur_set)) >= 1

    # verify iteration with pre_fetch
    comp_set = set()
    for sub_index in range(helper_count):
        source = FileSource.from_source(base_dir, fetch_file_list=True,
                                        index_filter=(helper_count, sub_index),
                                        search_mask="*.py")
        cur_set = set()
        for element in source:
            cur_set.add(element.filename)
        assert len(cur_set) > 0
        assert len(comp_set.intersection(cur_set)) == 0
        comp_set = comp_set.union(cur_set)
        assert len(comp_set.intersection(cur_set)) >= 1

    assert comp_set == prior_set

    assert len(full_set.intersection(prior_set)) == len(full_set)


def test_filtering():
    base_dir = os.path.normpath(os.path.dirname(__file__) + "/..")
    full_list = FileSource.from_source(base_dir, fetch_file_list=True,
                                       search_mask="*.py",
                                       filter_callback=lambda
                                           x: True)._file_list
    assert len(full_list) > 23
    # limit to first five entries, response with True and None
    five_element_list = \
        FileSource.from_source(base_dir, fetch_file_list=True,
                               search_mask="*.py",
                               filter_callback=lambda
                                   x: True if x.file_index < 5 else None).reduce_file_list()
    assert len(five_element_list) == 5
    # limit to first five entries, using boolean results
    five_element_list = FileSource.from_source(base_dir, fetch_file_list=True,
                                               search_mask="*.py",
                                               filter_callback=lambda
                                                   x: x.file_index < 5).reduce_file_list()
    assert len(five_element_list) == 5
    # limit to first five, rename them
    ren_source = FileSource.from_source(base_dir, fetch_file_list=True,
                                        search_mask="*.py",
                                        filter_callback=lambda
                                            x: "renamed_" + os.path.basename(
                                            x.element.filename))
    ren_source.reduce_file_list()
    assert ren_source.output_filename_list[0].startswith("renamed_")
    name_list = []
    with ren_source as source:
        for element in source:
            name_list.append(element.filename)
    assert name_list[0].startswith("renamed_")
    # test max_file_count using a file list
    new_list = FileSource.from_source(base_dir, fetch_file_list=True,
                                      search_mask="*.py",
                                      max_file_count=5).reduce_file_list()
    assert len(new_list) == 5 and new_list == five_element_list
    # test max_file_count using iterating
    element_count = 0
    new_list = FileSource.from_source(base_dir, fetch_file_list=False,
                                      search_mask="*.py",
                                      max_file_count=10)
    assert source.exists("__init__.py")
    assert not source.exists("NotExisting.py")
    for _ in new_list:
        element_count += 1
    assert element_count == 10


def test_source_disk():
    """
    Further FileSourceDisk tests
    """
    base_dir = os.path.normpath(os.path.dirname(__file__) + "/..")
    source = FileSource.from_source(base_dir,
                                    fetch_file_list=True, search_mask="*.py")
    source.handle_fetch_file_list()
    assert source.exists("__init__.py")
    assert not source.exists("NotExisting.py")
    with pytest.raises(FileNotFoundError):
        source.read_file("someNoneExistingFile.txt")
    abs_path = source.get_absolute("__index__.py")
    assert abs_path == FilePath.absolute(
        os.path.dirname(__file__) + "/../__index__.py")


def test_basic_functions():
    """
    Test abstract functions
    """
    file_source = FileSource()
    file_source.reduce_file_list()
    file_source.read_file("afile.txt")
    for _ in file_source:
        continue
    file_source.close()
    file_source.handle_fetch_file_list()
    # test if invalid protocol fails correctly
    with pytest.raises(NotImplementedError):
        file_source.from_source("wayne://")
    with pytest.raises(NotImplementedError):
        file_source.exists("anyFile.txt")


def test_statistics():
    """
    Tests the statistics creation
    """
    vl.sub_test("Testing get_statistics() and __str__ casting")
    test_source = FileSource.from_source(ESSENTIAL_DATA_ARCHIVE_NAME,
                                         fetch_file_list=True)
    statistics = str(test_source)
    vl.test.assert_val("essential_archive_statistics", statistics,
                       hash_val="dcc44322ca043dff16eb57ce972e10b7")
    list = test_source.get_file_list()
    assert len(list) == 3706
    # statistics twice
    assert test_source.get_statistics() is not None
    # no statistics
    test_source = FileSource.from_source(ESSENTIAL_DATA_ARCHIVE_NAME,
                                         fetch_file_list=False)
    assert test_source.get_statistics() is None


def test_file_list():
    """
    Tests the file list functionality
    """
    test_dir = os.path.dirname(__file__) + "/temp/dummy_dir/"
    try:
        shutil.rmtree(test_dir)
    except FileNotFoundError:
        pass
    os.makedirs(test_dir, exist_ok=True)
    FileStag.save(test_dir + "a.bin", data=b"123")
    FileStag.save(test_dir + "b.bin", data=b"123")
    FileStag.save(test_dir + "c.bin", data=b"123")
    fl_name = os.path.dirname(__file__) + "/temp/tflist.fin"
    FileStag.delete(fl_name)
    secret_path = SecretStr(test_dir)  # test usage of SecretStr
    file_source = FileSource.from_source(secret_path,
                                         fetch_file_list=True,
                                         file_list_name=(fl_name, 1))
    assert len(file_source.get_file_list()) == 3
    assert len(file_source) == 3
    assert "a.bin" in file_source
    FileStag.save(test_dir + "d.bin", data=b"123")
    file_source = FileSource.from_source(test_dir,
                                         fetch_file_list=True,
                                         file_list_name=(fl_name, 1))
    assert len(file_source.get_file_list()) == 3
    assert "d.bin" not in file_source
