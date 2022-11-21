"""
Tests the transaction functionality for a remote connection
"""
import time

import numpy as np
from scistag.tests.datastag.datastag4flask.shared_test_client import \
    test_client, test_remote_connection


def test_remote_transaction(test_remote_connection):
    """
    Tests the execution of a remote transaction
    """
    trc = test_remote_connection
    trc.set("rcTestValue", 456)
    trc.set("branch.rcSubTestValue", 456)
    with trc.start_transaction():
        trc.set("rcTestValue", 123)
        assert trc.get("rcTestValue")
        trc.set("branch.rcSubTestValue", 123)
        assert trc.get("rcSubTestValue")
        trc.add("branch.rcSubTestValue", 100)
    time.sleep(0.05)
    assert trc.get("rcTestValue") == 123
    assert trc.get("branch.rcSubTestValue") == 223
