import pytest
from scistag.datastag.data_stag_connection import DataStagConnection
import time
import json

try:
    from scistag.tests.datastag.local.vt_common import vault_connections
except ModuleNotFoundError:
    pass


# pylint: disable=W0621


def test_delete(vault_connections, connections=None):
    """
    Try deleting and detecting elements
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        assert connection.set("someElement", 456)
        assert connection.get("someElement", default=789) == 456
        assert connection.get("someNotExistingElement", default=789) == 789
        assert connection.get("someNotExistingElement") is None
        assert connection.exists("someElement")
        assert connection.delete("someElement")
        assert not connection.exists("someElement")


@pytest.mark.order(5)
def test_folder_structures(vault_connections, connections=None):
    """
    Tests the functionality of elements in folders (separated by dot)
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        for cur in ["a", "b", "c"]:
            server_name = f"server_{cur}"
            connection.set(
                f"services.inference.servers.{server_name}",
                {"name": server_name, "url": f"http://{server_name}:1234"},
            )
        values = connection.get_values_by_name("services.inference.servers.*")
        assert values[0]["name"] == "server_a"
        assert values[2]["name"] == "server_c"

        name_list = ["Peter", "Steffi", "Heinz", "Gitte", "Hans"]
        for cur in name_list:
            connection.set(f"users.{cur}", {"name": cur}, timeout_s=0.5)
        names = connection.find("users.*", relative_names=True)
        assert sorted(name_list) == sorted(names)
        names = connection.find("users.H*", relative_names=True)
        connection.find("users.*", relative_names=True)
        assert sorted(["Heinz", "Hans"]) == sorted(names)


def test_advanced_find(vault_connections, connections=None):
    """
    Tests if the element search works as expected
    :param vault_connections: The connections to be tested
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        connection.set("vcfx.a", 1)
        connection.set("vcfx.b", 1)
        connection.set("vcfx.c", 1)
        connection.set("vcfx.sub.a", 1)
        res_list = connection.find("vcfx.*", recursive=False)
        assert len(res_list) == 3
        assert all(["vcfx.a" in res_list, "vcfx.b" in res_list, "vcfx.c" in res_list])
        res_list = connection.find("vcfx.*", recursive=True)
        assert len(res_list) == 4
        assert "vcfx.sub.a" in res_list
        res_list = connection.find("vcfx.*", recursive=True, relative_names=True)
        assert len(res_list) == 4
        assert "sub.a" in res_list


def test_add(vault_connections, connections=None):
    """
    Tests if the add function which can increase or decrease a value in he db works as expected
    :param vault_connections: The connections to be tested
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        assert connection.add("counter", 2, default=5) == 7
        assert connection.add("counter") == 8
        assert connection.delete("counter")


@pytest.mark.order(10)
def test_garbage_collection(vault_connections, connections=None):
    """
    Tests if the garbage collection works as intended
    :param vault_connections: The connections to be tested
    """
    connections = connections if connections is not None else vault_connections
    prev_status = []
    for connection in connections:
        connection.set("someVar", "1234", 0.5)
        prev_status.append(connection.get_status())
    time.sleep(1.5)
    for index, connection in enumerate(connections):
        connection.collect_garbage()
        status = connection.get_status()
        assert status["elementCount"] < prev_status[index]["elementCount"]


def all_common_tests(connection):
    """
    Executes all other tests using the given connection
    :param connection: The connection
    """
    test_add(None, connections=[connection])
    test_delete(None, connections=[connection])
    test_folder_structures(None, connections=[connection])
    test_advanced_find(None, connections=[connection])
