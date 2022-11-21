import pytest
import time

try:
    from scistag.tests.datastag.local.vt_common import vault_connections
except ModuleNotFoundError:
    pass


def test_deprecation(vault_connections, connections=None):
    """
    Test element and list element deprecation after timeout
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        assert connection.set("depText", "someText", timeout_s=0.1)
        assert connection.get("depText") == "someText"
        assert connection.push("volatileList", [1, 2, 3], timeout_s=0.1)
        assert connection.push("volatileList", [4, 5, 6], timeout_s=0.2)
        assert connection.llen("volatileList") == 6
        assert connection.push("otherVolatileList", ["123", "456"], timeout_s=0.2)
        assert connection.push("thirdVolatileList", ["123", "456"], timeout_s=0.2)
    time.sleep(0.1)
    for connection in connections:
        assert connection.get("depText") is None
        assert connection.llen("volatileList") == 3
        assert connection.llen("otherVolatileList") == 2
        assert sum(connection.lelements("volatileList", 0, -1)) == 9
        assert sum(connection.lelements("volatileList", 0, None)) == 15
    time.sleep(0.1)
    for connection in connections:
        assert connection.pop("volatileList") is None
        assert connection.pop("volatileList", index=99, default=123) == 123
        assert connection.llen("volatileList") == 0
        assert connection.lelements("otherVolatileList", 0, None) == []
        assert connection.pop("otherVolatileList") is None
        assert connection.pop("thirdVolatileList") is None


def all_deprecation_tests(connection):
    """
    Executes all deprecation tests using the given connection
    :param connection: The connection
    """
    test_deprecation(None, connections=[connection])
