"""
Tests the add and timestamp functionality
"""
import time

import pytest

try:
    from scistag.tests.datastag.local.vt_common import vault_connections
except ModuleNotFoundError:
    pass


def test_add(vault_connections, connections=None):
    """
    General list testing
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        connection.set("orgIntValue", 45)
        assert connection.get("orgIntValue") == 45
        connection.add("orgIntValue", 10)
        assert connection.get("orgIntValue") == 55
        connection.set("orgFloatValue", 12.34)
        assert connection.get("orgFloatValue") == pytest.approx(12.34, 0.01)
        connection.add("orgFloatValue", 10)
        assert connection.get("orgFloatValue") == pytest.approx(22.34, 0.01)


def test_ts(vault_connections, connections=None):
    """
    Tests the timestamp functionality
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        connection.set_ts("tsValue", 123, timestamp=None)
        explicit_ts = time.time()
        connection.set_ts("tsValueExpl", 123, timestamp=explicit_ts)
        ts_time = connection.get_ts("tsValue", default=0.0)
        assert connection.get_ts("tsValueExpl", default=0.0) == explicit_ts
        assert ts_time != 0.0
        assert connection.get_ts_modified("tsValue", ts_time) == (ts_time, None)


def all_add_ts_tests(connection):
    """
    Executes all add and timestamp tests

    :param connection: The connection to test
    """
    test_add([connection])
    test_ts(([connection]))
