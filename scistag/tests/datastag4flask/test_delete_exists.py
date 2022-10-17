import pytest
import time
import numpy as np
from scistag.tests.datastag4flask.shared_test_client import test_client, test_remote_connection
from scistag.tests.datastag4flask.shared_data_dummies import get_dummy_jpg, get_dummy_np_array, get_dummy_dict


def test_delete_exists(test_remote_connection):
    trc = test_remote_connection
    assert trc.set("someValueToBeDeleted", 456)
    assert trc.exists("someValueToBeDeleted")
    assert trc.delete("someValueToBeDeleted")
    assert not trc.exists("someValueToBeDeleted")
