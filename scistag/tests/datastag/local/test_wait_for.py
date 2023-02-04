from threading import Thread

import pytest
import time

from scistag.common.time import sleep_min
from scistag.datastag import DataStagConnection

try:
    from scistag.tests.datastag.local.vt_common import vault_connections
except ModuleNotFoundError:
    pass


@pytest.mark.order(10)
def test_wait_for(vault_connections, connections=None):
    """
    Tests the wait_for feature
    """

    connections = connections if connections is not None else vault_connections
    for connection in connections:
        connection.delete("wfValue")
        assert connection.wait_for("wfValue", timeout_s=0.001, default=123) == 123
        connection.set("wfValue", 0)
        assert connection.wait_for("wfValue", timeout_s=0.001, default=123) == 0
        connection.delete("wfValue")
        assert connection.wait_for("wfValue", timeout_s=0.05, default=123) == 123
        connection.set("wfValue", 456)
        assert (
            connection.wait_for("wfValue", timeout_s=0.05, default=123, delete=True)
            == 456
        )
        connection.delete("wfValue")


def all_async_tests(connection):
    """
    Executes all other tests using the given connection
    :param connection: The connection
    """
    test_wait_for(None, connections=[connection])
