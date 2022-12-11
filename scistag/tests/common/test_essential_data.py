# Tests essential data authenticity and functionality
import zipfile
from scistag.common.essential_data import (
    verify_essential_data,
    ESSENTIAL_DATA_ARCHIVE_NAME,
)


def test_essential_data():
    """
    Tests if the data is available and valid
    """
    assert verify_essential_data()
    archive = zipfile.ZipFile(ESSENTIAL_DATA_ARCHIVE_NAME, "r")
    name_list = archive.namelist()
    name_set = set(name_list)
    assert 3600 < len(name_list) <= 3800
    assert "README.md" in name_set
    assert "LICENSE.md" in name_set
