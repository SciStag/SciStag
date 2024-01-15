"""
Checks the repositories health
"""

import os

import pytest

from scistag.common import ConfigStag
from scistag.gitstag import GitScanner
import scistag.tests

REPO_SIZE_LIMIT = 3000000
"The maximum repo limit of non-ignored files in byte"
REPO_DIR_COUNT_LIMIT = 350
"The maximum number of directories in the repo"
REPO_FILE_COUNT_LIMIT = 700
"The maximum number of files in the repo"
REPO_HARD_FILE_SIZE_LIMIT = 400000
"Maximum hard file size limit"

scistag.tests.ensure_config()


@pytest.mark.skipif(
    not bool(ConfigStag.get("testConfig.testGitIntegrity", True)),
    reason="Git integrity check disabled",
)
def test_repo_validity():
    """
    Tests if the repo is healthy to prevent accidental storage of garbage
    """
    scanner = GitScanner()
    base_path = os.path.normpath(os.path.dirname(__file__) + "/../../../")
    if not os.path.exists(base_path + "/.gitignore"):
        return
    scanner.scan(base_path)
    # check the repo does not exceed a reasonable size and
    # has a reasonable count of files and directories
    if scanner.total_size > REPO_SIZE_LIMIT:
        print("\n", flush=True)
        print(scanner.file_list_by_size[0:20], flush=True)
    assert scanner.total_size < REPO_SIZE_LIMIT
    assert REPO_FILE_COUNT_LIMIT // 2 < scanner.file_count
    assert scanner.file_count < REPO_FILE_COUNT_LIMIT
    assert REPO_DIR_COUNT_LIMIT // 2 < scanner.dir_count < REPO_DIR_COUNT_LIMIT
    lf_ignore_list = [
        "*/poetry.lock",
        "*/web/icons/Icon*",
        "*/AppIcon.appiconset/Icon*",
        "*/project.pbxproj",
        "*/data_stag_connection.py",
        "*/data_stag_vault.py",
        "*/imagestag/image.py",
        "*/slidestag/widget.py",
        "*/data/scistag_essentials.zip",
        "*/data/scistag_vector_emojis_0_0_2.zip",
        "*/file_source.py",
        "*/visual_log.py",
        "*/page_session.py",
        "*/log_builder.py",
        "*/cache.py",
    ]

    too_large_files = scanner.get_large_files(
        min_size=30000,
        hard_limit_size=REPO_HARD_FILE_SIZE_LIMIT,
        ignore_list=lf_ignore_list,
    )
    if len(too_large_files):
        print(too_large_files, flush=True)
    assert len(too_large_files) == 0
