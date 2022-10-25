"""
Tests the addon installation and removal and the integrity of the download URLs
and the archive's content
"""
import pytest
import os
from scistag.filestag import FileStag
from scistag.addons import AddonManager
from scistag.addons.addon_manager import (FEATURE_TEST, FEATURE_SIZE,
                                          FEATURE_INFO, FEATURE_MD5, GROUP_INFO)
from scistag.addons.addon_manager import (FEATURE_LOCAL_FILENAME,
                                          FEATURE_REMOTE_FILENAMES,
                                          GROUP_IGNORE_SET)
from scistag.logstag import log_info

# Environment variables
ENV_FLAG_TEST_ALL = "TEST_ALL_ADDONS"
"Environment variable. Set to 1 to test all downloadable addons."
ENV_FLAG_MAX_SIZE = "TEST_MAX_ADDON_SIZE"
"Environment variable. Set to a given byte size to limit the maximum size of downloaded archives."
ENV_FLAG_RELEASE_TEST = "TEST_RELEASE"
"Environment variable. Set to true to also execute long duration tests before a major release."


def test_db_validity():
    """
    Tests if the addon database contains reasonable data
    """
    addons = AddonManager.get_addon_data()
    assert addons is not None
    assert len(addons.keys()) >= 1  # at least one group should exist


def test_groups():
    """
    Tests if all defined groups provide all required information
    """
    for key, group in AddonManager.get_groups().items():
        assert len(key) > 0
        assert GROUP_INFO in group
        for f_key, feature in group.items():
            if f_key in GROUP_IGNORE_SET:
                continue
            assert FEATURE_INFO in feature
            assert FEATURE_REMOTE_FILENAMES in feature
            assert len(feature[FEATURE_REMOTE_FILENAMES]) > 0
            assert FEATURE_LOCAL_FILENAME in feature
            assert FEATURE_MD5 in feature
            assert FEATURE_SIZE in feature


@pytest.mark.order(10)
def test_install_and_removal():
    """
    Tests if the optional addons can be successfully installed and removed and if their data is valid.

    This test is only executed when the environment variable "TEST_RELEASE" is set to 1.
    Additional (environment) options:
        "TEST_ALL_ADDONS" - Also download very large addons (such as the 1024x1024 emojis)
        "TEST_MAX_ADDON_SIZE" - ... but set a maximum file size, e.g. to skip at least the more than 1 GB largr addons
    """
    release_test = int(os.environ.get(ENV_FLAG_RELEASE_TEST, "0")) == 1
    if not release_test:
        log_info(
            "\nSkipping addon install and removal test due to traffic. Set TEST_RELEASE to 1 to execute all tests.\n")
        return
    intense_test = int(os.environ.get(ENV_FLAG_TEST_ALL, "0")) == 1
    max_size = int(os.environ.get(ENV_FLAG_MAX_SIZE, "0"))
    if intense_test:
        log_info(
            "Full addon verification test enabled. This could take a while...")

    keep = set()
    for key, feature in AddonManager.get_all_addons().items():
        if AddonManager.get_addon_installed(key):
            keep.add(key)

    # remove addons we want to install
    for key, feature in AddonManager.get_all_addons().items():
        if not feature.get(FEATURE_TEST, False) and not intense_test:
            continue
        if max_size != 0 and feature[FEATURE_SIZE] > max_size:
            continue
        if AddonManager.get_addon_installed(
                key):  # remove addons we want to install ourselves
            AddonManager.remove_addon(key)

    # install test addons
    for key, feature in AddonManager.get_all_addons().items():
        if not feature.get(FEATURE_TEST, False) and not intense_test:
            continue
        if max_size != 0 and feature[FEATURE_SIZE] > max_size:
            log_info(
                f"Feature {key} exceeds maximum test size of {max_size} bytes, skipping download test.")
            continue
        assert AddonManager.install_addon(key)

    # load addons so we can also test the registration and un-registration process in SharedArchive
    paths = AddonManager.get_addons_paths("emojis.*")
    assert len(paths) != 0

    # uninstall test addons
    for key, feature in AddonManager.get_all_addons().items():
        if key in keep:
            log_info(f"{key} was installed before the tests - keeping addon.")
            continue
        if not feature.get(FEATURE_TEST, False) and not intense_test:
            continue
        if max_size != 0 and feature[FEATURE_SIZE] > max_size:
            continue
        assert AddonManager.remove_addon(key)

    log_info("\n")


@pytest.mark.order(11)
def test_addon_access():
    """
    Tests if the addons data can be accessed
    """
    AddonManager.install_addon("emojis.svg")
    paths = AddonManager.get_addons_paths("emojis.svg")
    assert len(paths) == 1
    assert "emojis.svg" in paths
    svg_path = paths["emojis.svg"]
    test_file = FileStag.load(
        svg_path + "images/noto/emojis/svg/emoji_u00a9.svg")
    assert len(test_file) == 2483
    installed_addons = AddonManager.get_installed_addons()
    assert "emojis.svg" in installed_addons
