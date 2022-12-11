import logging
import os
from threading import RLock

from scistag.common.configuration import (
    ESSENTIAL_DATA_URL,
    ESSENTIAL_DATA_ARCHIVE_NAME,
    ESSENTIAL_DATA_MD5,
    ESSENTIAL_DATA_SIZE,
)
import hashlib

data_prepared_lock = RLock()
data_prepared = False


def _prepare_essential_data() -> bool:
    """
    Downloads the essential data required for SciStag from the web
    :return: True on success
    """
    global data_prepared
    global data_prepared_lock
    with data_prepared_lock:
        if data_prepared:
            return True
        if not os.path.exists(ESSENTIAL_DATA_ARCHIVE_NAME):
            verify_essential_data()
        from scistag.filestag import SharedArchive

        SharedArchive.register(
            ESSENTIAL_DATA_ARCHIVE_NAME, "scistagessential", cache=False
        )
        success = os.path.exists(ESSENTIAL_DATA_ARCHIVE_NAME)
        data_prepared = True
        return success


def verify_data(
    identifier, archive_name, source_url, exp_size, exp_md5, quick=False
) -> bool:
    """
    Verifies the SciStag data is available, downloads it if not and verifies
    it's integrity

    :param identifier: The zip archive's global identifier
    :param archive_name: The archive's name
    :param source_url: The url at where the current data set is provided
    :param quick: Defines if a fast check shall be executed
    :param exp_size: The expected file size
    :param exp_md5: The expected md5 value
    :return: True on success
    """
    from scistag.webstag.web_fetch import web_fetch

    path = archive_name
    file_size = os.path.getsize(path) if os.path.exists(path) else 0
    invalid_filesize = file_size != exp_size
    if invalid_filesize:
        logging.warning(
            f"Data file {archive_name} is invalid. Removing and re-downloading it."
        )
    if not os.path.exists(path):
        logging.info(f"Downloading {source_url}...")
        web_fetch(source_url, filename=path)
    if not quick:
        digest = hashlib.md5(open(path, "rb").read()).hexdigest()
        valid = digest == exp_md5
        if not valid:
            raise Exception(f"MD5 checksum verification for {archive_name} failed")
    from scistag.filestag import SharedArchive

    SharedArchive.register(archive_name, identifier, cache=False)
    return os.path.exists(path)


def verify_essential_data(quick=False) -> bool:
    """
    Verifies the SciStag data is available, downloads it if not and verifies it's integrity
    :param quick: Defines if a fast check shall be executed
    :return: True on success
    """
    return verify_data(
        identifier="scistagessential",
        archive_name=ESSENTIAL_DATA_ARCHIVE_NAME,
        source_url=ESSENTIAL_DATA_URL,
        exp_size=ESSENTIAL_DATA_SIZE,
        exp_md5=ESSENTIAL_DATA_MD5,
        quick=quick,
    )


_ESSENTIAL_DATA_PATH = "zip://@scistagessential/"


def get_edp() -> str:
    """
    Verifies if the essential data archive was initialized and afterwards returns the FileStag access path to it.
    :return: The base path to access data within the essential data archive. See filestag.FileStag
    """
    _prepare_essential_data()
    return _ESSENTIAL_DATA_PATH
