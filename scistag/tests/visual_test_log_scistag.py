"""
Implements the class :class:`VisualTestLog` which helps creating unit tests
foe visual data by automatically creating hash sums for images and reference
dumps for dataframes and numpy arrays.
"""

import hashlib

from scistag.common import ConfigStag
from scistag.vislog import VisualTestLog
from scistag.tests.config import ensure_config

ensure_config()


class VisualTestLogSciStag(VisualTestLog):
    """
    Helper class for the visualization of unit test results
    """

    def __init__(self, test_filename: str, **params):
        """
        :param test_filename: The name of the test file.
            From this the VisualTestLog automatically extracts the relative
             target path and test name
        :param params: Advanced parameters, see :class:`VisualLog`
        """
        log_images = bool(ConfigStag.get("testConfig.logImages", False))
        super().__init__(test_filename=test_filename,
                         log_images=log_images,
                         **params)
