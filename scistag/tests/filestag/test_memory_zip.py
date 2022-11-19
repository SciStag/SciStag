"""
Tests the MemoryZip class
"""
import os.path

from scistag.filestag import FileSource, MemoryZip


def test_mem_zip():
    """
    Tests the basic functions
    """
    fs = FileSource.from_source(os.path.dirname(__file__), search_mask="*.py",
                                recursive=False)
    total_size = 0
    with MemoryZip() as mz:
        for element in fs:
            total_size += len(element.data)
            mz.writestr(element.filename, element.data)
    extracted = MemoryZip(source=mz.to_bytes())
    name_list = extracted.namelist()
    ext_total_size = 0
    for element in fs:
        assert element.filename in name_list
        info = extracted.NameToInfo[element.filename]
        ext_total_size += info.file_size
    assert ext_total_size == total_size
