import pytest

from scistag.common.time import sleep_min

try:
    from scistag.tests.datastag.local.vt_common import vault_connections
except ModuleNotFoundError:
    pass


@pytest.mark.order(0)
def test_set(vault_connections, connections=None):
    """
    Try setting of different data types
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        assert connection.set("someString", "123")
        assert connection.set("someInt", 1234)
        assert connection.set("someBool", True)
        assert connection.set("someNegativeBool", False)
        assert connection.set("someFloat", 123.345)
        assert connection.set("someBytes", b"123")
        assert connection.set("someDict", {"value": 123})


@pytest.mark.order(1)
def test_get(vault_connections, connections=None):
    """
    Try reading previously set types
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        assert connection.get("someString") == "123"
        assert connection.get("someInt") == 1234
        assert connection.get("someBool")
        assert not connection.get("someNegativeBool")
        assert connection.get("someFloat") == 123.345
        assert connection.get("someBytes") == b"123"
        assert connection.get("someDict")["value"] == 123


def test_get_ex(vault_connections, connections=None):
    """
    Tests if the get_ex function which is able to selectively only receive a value if it was modified works as
    expected.
    :param vault_connections: The connections to be tested
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        v = 0
        connection.set("modifyingValue", 5)
        v, value = connection.get_ex("modifyingValue", version_counter=v)
        assert value == 5
        v, value = connection.get_ex("modifyingValue", version_counter=v)
        assert value is None
        connection.set("modifyingValue", 6)
        new_v, value = connection.get_ex("modifyingValue", version_counter=v)
        assert new_v == v + 1 and value == 6
        assert connection.get_ex("doesntExist") == (0, None)
        connection.set("deprValue", 22, timeout_s=0.1)
        assert connection.get_ex("deprValue") == (1, 22)
        sleep_min(0.1)
        assert connection.get_ex("deprValue") == (0, None)


def all_get_set_tests(connection):
    """
    Executes all get set tests using the given connection
    :param connection: The connection
    """
    test_set(vault_connections=None, connections=[connection])
    test_get(vault_connections=None, connections=[connection])
    test_get_ex(vault_connections=None, connections=[connection])
