"""
Tests the class DataStagConnection
"""
import time
from threading import Thread

import pytest

from scistag.datastag import DataStagConnection

try:
    from scistag.tests.datastag.local.vt_common import vault_connections
except ModuleNotFoundError:
    pass


class TaInterruptThread(Thread):
    """
    Helper thread which shall try do modify data in between a transaction
    (which should not be possible).
    """

    def __init__(self, connection: DataStagConnection):
        super().__init__()
        self.connection: DataStagConnection = connection

    def run(self) -> None:
        self.connection.set("staTestValue", 456)
        self.connection.set("staBranch.otherValue", 456)


@pytest.mark.order(0)
def test_transaction(vault_connections, connections=None):
    """
    Try setting of different data types
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        # try to let a thread modify data within an transaction (which should
        # have no affect until we finish it)
        with connection.start_transaction():
            connection.set("staTestValue", 123)
            connection.set("staBranch.otherValue", 123)
            it = TaInterruptThread(connection)
            it.start()
            time.sleep(0.05)
            assert connection.get("staTestValue") == 123
            assert connection.get("staBranch.otherValue") == 123
        it.join()
        time.sleep(0.05)
        assert connection.get("staTestValue") == 456
        assert connection.get("staBranch.otherValue") == 456
        # try the same w/o transaction
        connection.set("staTestValue", 123)
        connection.set("staBranch.otherValue", 123)
        it = TaInterruptThread(connection)
        it.start()
        time.sleep(0.05)
        assert connection.get("staTestValue") == 456
        assert connection.get("staBranch.otherValue") == 456
        it.join()

