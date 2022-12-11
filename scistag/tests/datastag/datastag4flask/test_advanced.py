import pytest
from scistag.tests.datastag.datastag4flask.shared_test_client import (
    test_client,
    test_remote_connection,
)
import time
import numpy as np
from scistag.tests.datastag.datastag4flask.shared_data_dummies import (
    get_dummy_jpg,
    get_dummy_np_array,
    get_dummy_dict,
)


@pytest.mark.order(20)
def test_advanced(test_remote_connection):
    trc = test_remote_connection
    trc.set("folder.value", "123")
    trc.collect_garbage()
    status = trc.get_status()
    assert isinstance(status, dict) and status["folderCount"] > 0
