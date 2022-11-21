"""
Tests the basic functionality to access a DataStag connection
"""
from scistag.datastag import DataStagConnection


def test_connection():
    """
    Tests the DataStag connection
    """
    con = DataStagConnection()
    con.set("aTestValue", "123")
    assert con.get("aTestValue") == "123"
