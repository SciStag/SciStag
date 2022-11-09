"""
Tests VisualLog's testing capabilities for regression tests
"""

import shutil
from unittest import mock

import numpy as np
import pytest

from . import vl


def test_general_assertion():
    """
    Tests basic type assertion
    """
    with pytest.raises(NotImplementedError):
        vl.test.assert_val("abool", True)
