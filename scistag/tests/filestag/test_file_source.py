"""
Tests the :class:`FileSource` class.

With the :class:`FileSource` class you can iterate through directories, archives or cloud storage sources
file by file with a minimum of code.
"""
import hashlib
import os.path
import shutil
import time
from unittest import mock

import pytest
from pydantic import SecretStr

from scistag.filestag import FileSource, FileStag, FilePath, FileSink

from . import vl
from ...common import ESSENTIAL_DATA_ARCHIVE_NAME
from ...common.time import sleep_min
from ...filestag.file_source import FileSourcePathOptions, FileListEntry


def test_scan():
    """
    Tests the basic scanning functionality
    """
    base_dir = os.path.normpath(os.path.dirname(__file__) + "/..")

    filter_callback = lambda fi: not any(
        [
            "visual_micro" not in fi.element.filename,
            "log" not in fi.element.filename,
            "temp" not in fi.element.filename,
        ]
    )

    source = FileSource.from_source(
        base_dir,
        recursive=False,
        fetch_file_list=True,
        filter_callback=filter_callback,
    )
    assert len(source._file_list) >= 1
    assert len(source._file_list) < 20

    source = FileSource.from_source(
        base_dir,
        recursive=True,
        fetch_file_list=True,
        filter_callback=filter_callback,
    )
    assert len(source._file_list) >= 90
    assert len(source._file_list) < 550


def test_iteration():
    """
    Tests the iteration through a list of files
    """
    base_dir = os.path.normpath(os.path.dirname(__file__) + "/../filestag")
    source = FileSource.from_source(
        base_dir, recursive=True, fetch_file_list=True, search_mask="*.py"
    )
    assert len(source._file_list) >= 3
    assert len(source._file_list) < 20

    total_size = 0
    total_count = 0
    for element in source:
        total_count += 1
        total_size += len(element.data)

    assert 3 <= total_count <= 20
    assert total_size >= 5000


def test_context():
    """
    Tests entering and leaving the context
    """
    base_dir = os.path.normpath(os.path.dirname(__file__) + "/../filestag")
    source = FileSource.from_source(
        base_dir, recursive=True, fetch_file_list=True, search_mask="*.py"
    )
    assert not source.is_closed
    with source:
        pass
    assert source.is_closed
    with source:
        pass


def test_sharing():
    """
    Tests sharing a task between multiple helpers
    """
    helper_count = 3

    base_dir = os.path.normpath(os.path.dirname(__file__))
    full_list = FileSource.from_source(
        base_dir, fetch_file_list=True, search_mask="*.py"
    )._file_list
    full_set = set([element.filename for element in full_list])

    prior_set = set()
    # verify file list pre-fetch with skip
    for sub_index in range(helper_count):
        part_list = FileSource.from_source(
            base_dir,
            fetch_file_list=True,
            index_filter=(helper_count, sub_index),
            search_mask="*.py",
        ).reduce_file_list()
        cur_set = set([element.filename for element in part_list])
        assert len(cur_set) > 0
        assert len(prior_set.intersection(cur_set)) == 0
        prior_set = prior_set.union(cur_set)
        assert len(prior_set.intersection(cur_set)) >= 1

    assert len(full_set.intersection(prior_set)) == len(full_set)
    # verify iteration with skip
    prior_set = set()
    for sub_index in range(helper_count):
        source = FileSource.from_source(
            base_dir, index_filter=(helper_count, sub_index), search_mask="*.py"
        )
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
        source = FileSource.from_source(
            base_dir,
            fetch_file_list=True,
            index_filter=(helper_count, sub_index),
            search_mask="*.py",
        )
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
    full_list = FileSource.from_source(
        base_dir,
        fetch_file_list=True,
        search_mask="*.py",
        filter_callback=lambda x: True,
    )._file_list
    assert len(full_list) > 23
    # limit to first five entries, response with True and None
    five_element_list = FileSource.from_source(
        base_dir,
        fetch_file_list=True,
        search_mask="*.py",
        filter_callback=lambda x: True if x.file_index < 5 else None,
    ).reduce_file_list()
    assert len(five_element_list) == 5
    # limit to first five entries, using boolean results
    five_element_list = FileSource.from_source(
        base_dir,
        fetch_file_list=True,
        search_mask="*.py",
        filter_callback=lambda x: x.file_index < 5,
    ).reduce_file_list()
    assert len(five_element_list) == 5
    # limit to first five, rename them
    ren_source = FileSource.from_source(
        base_dir,
        fetch_file_list=True,
        search_mask="*.py",
        filter_callback=lambda x: "renamed_" + os.path.basename(x.element.filename),
    )
    ren_source.reduce_file_list()
    assert ren_source.output_filename_list[0].startswith("renamed_")
    name_list = []
    with ren_source as source:
        for element in source:
            name_list.append(element.filename)
    assert name_list[0].startswith("renamed_")
    # test max_file_count using a file list
    new_list = FileSource.from_source(
        base_dir, fetch_file_list=True, search_mask="*.py", max_file_count=5
    ).reduce_file_list()
    assert len(new_list) == 5 and new_list == five_element_list
    # test max_file_count using iterating
    element_count = 0
    new_list = FileSource.from_source(
        base_dir, fetch_file_list=False, search_mask="*.py", max_file_count=10
    )
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
    source = FileSource.from_source(base_dir, fetch_file_list=True, search_mask="*.py")
    source.handle_fetch_file_list()
    assert source.exists("__init__.py")
    assert not source.exists("NotExisting.py")
    with pytest.raises(FileNotFoundError):
        source.fetch("someNoneExistingFile.txt")
    abs_path = source.get_absolute("__index__.py")
    assert abs_path == FilePath.absolute(os.path.dirname(__file__) + "/../__index__.py")


def test_basic_functions():
    """
    Test abstract functions
    """
    file_source = FileSource()
    file_source.reduce_file_list()
    file_source.fetch("afile.txt")
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
    test_source = FileSource.from_source(
        ESSENTIAL_DATA_ARCHIVE_NAME, fetch_file_list=True
    )
    statistics_str = str(test_source)
    assert (
        hashlib.md5(statistics_str.encode("utf-8")).hexdigest()
        == "dc94728e1ed121e8f9a7e434b8ccf264"
    )
    statistics = test_source.get_statistics()
    vl.test.assert_val(
        "essential_archive_statistics",
        statistics,
        hash_val="1877a538d0b9ebdc674841243fc27b35",
    )
    list = test_source.file_list
    assert len(list) == 3706
    # statistics twice
    assert test_source.get_statistics() is not None
    # no statistics
    test_source = FileSource.from_source(
        ESSENTIAL_DATA_ARCHIVE_NAME, fetch_file_list=False
    )
    assert test_source.get_statistics() is None
    test_source.refresh()
    assert test_source.get_statistics() is not None


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
    file_source = FileSource.from_source(
        secret_path, fetch_file_list=True, file_list_name=(fl_name, 1)
    )
    assert len(file_source.file_list) == 3
    assert len(file_source) == 3
    assert "a.bin" in file_source
    FileStag.save(test_dir + "d.bin", data=b"123")
    file_source = FileSource.from_source(
        test_dir, fetch_file_list=True, file_list_name=(fl_name, 1)
    )
    assert len(file_source.file_list) == 3
    assert "d.bin" not in file_source
    file_source = FileSource.from_source(
        test_dir, fetch_file_list=True, file_list_name=fl_name
    )
    assert len(file_source.file_list) == 3
    FileSource.from_source(test_dir, fetch_file_list=True, file_list_name=(fl_name, 2))


def test_hash(tmp_path):
    """
    Test's the file source's hash functionality
    """
    tar_dir = str(tmp_path) + "/obsdir"
    try:
        shutil.rmtree(tar_dir)
    except FileNotFoundError:
        pass
    os.makedirs(tar_dir, exist_ok=True)
    FileStag.save(tar_dir + "/testa.bin", b"123")
    FileStag.save(tar_dir + "/testb.bin", b"456")
    source = FileSource.from_source(tar_dir)
    hash_val = source.get_hash()
    assert source.__hash__() == hash_val
    source.refresh()
    assert source.get_hash() == hash_val
    source.refresh()
    for tries in range(15):
        FileStag.save(tar_dir + "/testb.bin", b"789")
        if source.get_hash() != hash_val:
            break
        sleep_min(0.1)
        source.refresh()
    assert not source.get_hash() == hash_val
    hash_val = source.get_hash(max_content_size=10)
    FileStag.save(tar_dir + "/testb.bin", b"555")
    assert source.get_hash(max_content_size=10) != hash_val


def test_copy_to(tmp_path):
    """
    Tests the copying capabilities of FileSource
    """
    test_target = str(tmp_path) + "/copyTest"
    try:
        shutil.rmtree(test_target)
    except FileNotFoundError:
        pass
    source = FileSource.from_source(
        ESSENTIAL_DATA_ARCHIVE_NAME,
        search_path="fonts/",
        sorting_callback=lambda x: x.filename,
    )

    assert len(source.file_list) == 20
    os.makedirs(test_target, exist_ok=True)
    source.copy("Roboto/LICENSE.txt", test_target + "/TestFile.txt")
    assert len(FileStag.load(test_target + "/TestFile.txt")) == 11560
    try:
        shutil.rmtree(test_target)
    except FileNotFoundError:
        pass
    sink = FileSink.with_target(test_target)
    source.copy_to(sink)
    assert len(FileStag.load(test_target + "/Roboto/LICENSE.txt")) == 11560
    copies = FileSource.from_source(test_target)
    assert len(copies.file_list) == len(source.file_list)
    try:
        shutil.rmtree(test_target)
    except FileNotFoundError:
        pass
    copies = FileSource.from_source(test_target)
    assert len(copies.file_list) == 0
    source.copy_to(test_target)
    copies = FileSource.from_source(test_target, max_web_cache_age=60)
    assert len(copies.fetch("Roboto/LICENSE.txt")) == 11560
    assert len(copies.fetch("Roboto/LICENSE.txt")) == 11560
    assert len(copies.file_list) == len(source.file_list)
    try:
        shutil.rmtree(test_target)
    except FileNotFoundError:
        pass
    source.copy_to(test_target, overwrite=False)
    source.copy_to(test_target, overwrite=False)
    copies = FileSource.from_source(test_target)
    assert len(copies.file_list) == len(source.file_list)
    try:
        shutil.rmtree(test_target)
    except FileNotFoundError:
        pass
    with mock.patch("os.makedirs"):  # prevent storage
        error_list = []
        source.copy_to(test_target, error_log=error_list)
        assert len(error_list) > 0
    with mock.patch.object(source, "fetch", lambda x: None):
        error_list = []
        source.copy_to(test_target, error_log=error_list)
        assert len(error_list) > 0


def test_copy_errors(tmp_path):
    """
    Provokes file source copying errors to verify them
    """
    test_target = str(tmp_path) + "/copyTest"
    try:
        shutil.rmtree(test_target)
    except FileNotFoundError:
        pass
    source = FileSource.from_source(
        ESSENTIAL_DATA_ARCHIVE_NAME,
        search_path="fonts/",
        sorting_callback=lambda x: x.filename,
    )
    assert len(source.file_list) == 20
    os.makedirs(test_target, exist_ok=True)
    source.copy("Roboto/LICENSE.txt", test_target + "/TestFile.txt")
    target = FileSink.with_target("zip://", compression=0)
    with mock.patch.object(source, "fetch", lambda x: None):
        error_list = []
        source.copy_to(target, error_log=error_list)
        assert len(error_list) > 0
    target = FileSink.with_target("zip://", compression=0)
    with mock.patch.object(target, "store", lambda x, d, overwrite: False):
        error_list = []
        source.copy_to(target, error_log=error_list)
        assert len(error_list) > 0
    with mock.patch.object(source, "fetch", lambda x: None):
        error_list = []
        source.copy_to(target, error_log=error_list, overwrite=False)
        assert len(error_list) > 0
    with mock.patch.object(target, "store", lambda x, d, overwrite: False):
        error_list = []
        source.copy_to(target, error_log=error_list, overwrite=False)
        assert len(error_list) > 0
    with mock.patch.object(source, "fetch", lambda x: None):
        error_list = []
        source.copy_to(test_target, error_log=error_list, overwrite=False)
        assert len(error_list) > 0
    with mock.patch("scistag.filestag.FileStag.save", lambda x, d, overwrite: False):
        error_list = []
        source.copy_to(test_target, error_log=error_list, overwrite=False)
        assert len(error_list) > 0


def test_custom_file_list():
    """
    Tests setting an own file list
    """
    cur_path = os.path.dirname(__file__)
    local_source = FileSource.from_source(cur_path)
    assert local_source.exists("test_file_stag.py")
    assert len(local_source.file_list) > 20
    local_source.set_file_list(["test_file_source.py"])
    assert not local_source.exists("test_file_stag.py")
    assert local_source.exists("test_file_source.py")
    entries = [FileListEntry(filename="test_file_stag.py", file_size=123)]
    local_source.set_file_list(entries)
    assert local_source.exists("test_file_stag.py")
    assert not local_source.exists("test_file_source.py")


def test_sorting():
    """
    Tests the sorting functions
    """
    with pytest.raises(ValueError):
        FileSource.from_source(
            ESSENTIAL_DATA_ARCHIVE_NAME,
            search_path="fonts/",
            sorting_callback=lambda x: x.filename,
            fetch_file_list=False,
        )
    source = FileSource.from_source(
        ESSENTIAL_DATA_ARCHIVE_NAME,
        search_path="fonts/",
        sorting_callback=lambda x: x.filename,
        fetch_file_list=True,
    )
    assert source.file_list[0].filename == "JetBrains Mono/AUTHORS.txt"


def test_copy(tmp_path):
    """
    Tests the single file copying capabilities of FileSource
    """
    test_target = str(tmp_path) + "/copyTest"
    try:
        shutil.rmtree(test_target)
    except FileNotFoundError:
        pass
    source = FileSource.from_source(
        ESSENTIAL_DATA_ARCHIVE_NAME,
        search_path="fonts/",
        sorting_callback=lambda x: x.filename,
    )
    sink = FileSink.with_target(test_target)
    fetched = False

    def on_fetch(fn):
        nonlocal fetched
        fetched = True

    fetch_done = False
    fetch_size = 0

    def on_fetch_done(fn, size):
        nonlocal fetch_done, fetch_size
        fetch_done = True
        fetch_size = size

    error = False

    def on_error(fn, text):
        nonlocal error
        error = True

    skipped = False

    def on_skip(fn):
        nonlocal skipped
        skipped = True

    stored_fn = ""
    stored_size = 0

    def on_stored(fn, size):
        nonlocal stored_fn, stored_size
        stored_fn = fn
        stored_size = size

    source.copy(
        "Roboto/LICENSE.txt",
        test_target + "out1.txt",
        on_fetch=on_fetch,
        on_fetch_done=on_fetch_done,
    )
    assert fetched
    assert fetch_done
    assert fetch_size > 50

    source.copy(
        "Roboto/LICENSE.txt",
        test_target + "out1.txt",
        on_fetch=on_fetch,
        on_fetch_done=on_fetch_done,
        overwrite=False,
        on_skip=on_skip,
    )
    assert skipped
    source.copy(
        "Roboto/LICENSE.txt",
        test_target + "out1.txt",
        on_fetch=on_fetch,
        on_fetch_done=on_fetch_done,
        overwrite=False,
    )
    source.copy(
        "Roboto/LICENSE.txt",
        test_target + "out1.txt",
        on_fetch=on_fetch,
        on_fetch_done=on_fetch_done,
        on_error=on_error,
        on_stored=on_stored,
    )
    assert len(stored_fn) > 0
    assert stored_size == 11560
    assert not error
    sink = FileSink.with_target(test_target)
    source.copy("Roboto/LICENSE.txt", "out_sink.txt", sink=sink)
    assert len(FileStag.load(test_target + "/out_sink.txt")) == 11560
    with mock.patch.object(source, "fetch", lambda fn: None):
        source.copy(
            "Roboto/LICENSE.txt",
            test_target + "out1.txt",
            on_fetch=on_fetch,
            on_fetch_done=on_fetch_done,
            on_error=on_error,
        )
    assert error
    error = False
    with mock.patch(
        "scistag.filestag.FileStag.save", lambda fn, data, overwrite: False
    ):
        source.copy(
            "Roboto/LICENSE.txt",
            test_target + "out1.txt",
            on_fetch=on_fetch,
            on_fetch_done=on_fetch_done,
            on_error=on_error,
        )
    assert error
    with mock.patch.object(source, "fetch", lambda fn: None):
        source.copy("Roboto/LICENSE.txt", test_target + "out1.txt")
    assert error
    error = False
    with mock.patch(
        "scistag.filestag.FileStag.save", lambda fn, data, overwrite: False
    ):
        source.copy("Roboto/LICENSE.txt", test_target + "out1.txt", on_error=on_error)
    assert error


def test_path_options():
    """
    Tests the path options class
    """
    FileSourcePathOptions(for_file_stag=True)


def test_absolute_paths():
    """
    Tests the absolute path functionality
    """
    test_source = FileSource()
    assert test_source.get_absolute("") is None
    test_source = FileSource.from_source(os.path.dirname(__file__))
    assert len(test_source.get_absolute("test_file_source.py")) > 20
