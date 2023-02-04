import pytest
import numpy as np
import pandas as pd

try:
    from scistag.tests.datastag.local.vt_common import vault_connections
except ModuleNotFoundError:
    pass


def test_list_basics(vault_connections, connections=None):
    """
    General list testing
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        assert connection.push("someList", ["stringValue"]) == 1
        assert connection.lelements("someList", 0, 1)[0] == "stringValue"
        assert connection.push("someList", ["intValue"]) == 2
        assert connection.llen("someList") == 2
        assert connection.pop("someList") == "stringValue"
        assert connection.llen("someList") == 1
        assert not connection.delete("notExistingElement")
        assert connection.delete("someList")

        series = pd.Series([1, 3, 5, np.nan, 6, 8])
        df = pd.DataFrame(
            {
                "A": 1.0,
                "B": pd.Timestamp("20130102"),
                "C": pd.Series(1, index=list(range(4)), dtype="float32"),
                "D": np.array([3] * 4, dtype="int32"),
                "E": pd.Categorical(["test", "train", "test", "train"]),
                "F": "foo",
            }
        )

        data = {
            "command": "set",
            "value": b"123",
            "npa": np.array(["123.456", "789.0"]),
            "pd": df,
            "pds": series,
        }
        assert connection.push("dataList", data)
        fetched_data = connection.pop("dataList")
        for element in fetched_data.keys():
            cur_ele = fetched_data[element]
            if isinstance(cur_ele, (pd.Series, pd.DataFrame)):
                assert cur_ele.equals(data[element])
            elif isinstance(cur_ele, np.ndarray):
                assert np.all(fetched_data[element] == data[element])
            else:
                assert cur_ele == data[element]
        np_data = np.array(["123.456", "789.0"])
        assert connection.push("dataList", np_data)
        received_data = connection.pop("dataList")
        assert all(received_data == np_data)
        assert connection.push("dataList", series)
        received_data = connection.pop("dataList")
        assert received_data.equals(series)
        assert connection.push("dataList", df)
        received_data = connection.pop("dataList")
        assert received_data.equals(df)


def test_list_delete(vault_connections, connections=None):
    """
    List object removal functions
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        assert connection.push("delList", ["stringValue"]) == 1
        assert connection.delete("delList")
        assert connection.llen("delList") == 0


def test_list_delete_multiple(vault_connections, connections=None):
    """
    List object removal functions
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        assert connection.set("folderX.A", 5)
        assert connection.set("folderA.A", 1)
        assert connection.set("folderA.B", 2)
        assert connection.set("folderA.C", 3)
        assert connection.exists("folderA.A")
        assert connection.set("folderA.subFolder.X", 3)
        assert connection.delete_multiple(["folderA.*"], recursive=False) == 3
        assert not connection.exists("folderA.A")
        assert connection.set("folderA.A", 1)
        assert connection.set("folderA.B", 2)
        assert connection.set("folderA.C", 3)
        assert connection.exists("folderA.A")
        assert connection.delete_multiple("", recursive=True) == 0
        assert connection.delete_multiple("./", recursive=True) == 0
        assert connection.delete_multiple("*", recursive=True) == 0
        assert connection.delete_multiple(["folderA.*"], recursive=True) == 4


def test_list_insert(vault_connections, connections=None):
    """
    List inserting and removal
    """
    connections = connections if connections is not None else vault_connections
    for connection in connections:
        assert connection.push("insList", ["stringValue", "helloWorld"]) == 2
        assert connection.push("insList", ["firstValue", "secondValue"], index=0) == 4
        assert connection.push("insList", ["midValueA", "midValueB"], index=2) == 6
        assert (
            " ".join(connection.lelements("insList", start=1, end=3))
            == "secondValue midValueA"
        )
        assert connection.pop("insList", index=2)
        assert (
            " ".join(connection.lelements("insList", start=1, end=3))
            == "secondValue midValueB"
        )
        assert connection.delete("insList")


def all_list_tests(connection):
    """
    Executes all list tests using the given connection
    :param connection: The connection
    """
    test_list_basics(None, connections=[connection])
    test_list_insert(None, connections=[connection])
    test_list_delete(None, connections=[connection])
    test_list_delete_multiple(None, connections=[connection])
