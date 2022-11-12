"""
Tests the :class:`ConfigStag` class
"""
import copy
import os.path

import pytest

from scistag.common import ConfigStag


def test_set_get():
    """
    Tests basic set and get commands
    """
    ConfigStag.set("testAppName", "testApp")
    assert ConfigStag.get("testAppName") == "testApp"
    assert ConfigStag.get("testAppNameX") is None
    assert ConfigStag.get("testAppNameY", 123) == 123
    ConfigStag.set("sampleConfig.database.connectionString", "456")
    assert ConfigStag.get("sampleConfig.database.connectionString") == "456"
    with pytest.raises(ValueError):
        _ = ConfigStag.get("branch.")
    with pytest.raises(ValueError):
        ConfigStag.set("otherBranch.", "x")
    ConfigStag._get_branch(ConfigStag.root_branch, "")


def test_load():
    """
    Tests loading a file from disk
    """
    config_path = os.path.dirname(__file__) + "/dummy_config.json"
    ConfigStag.load_config_file(config_path, "testImport")
    assert ConfigStag.get("testImport.tests.connections.testConnection") == "connection://123"
    os.environ["SC_TEST_TESTCONNECTION"] = "connection://otherConnection"
    ConfigStag.load_config_file(config_path, "testImport", environment="SC_TEST_")
    assert ConfigStag.get("testImport.testconnection") == "connection://otherConnection"
    os.environ["SC_TEST_CONNECTIONS_TESTCONNECTION"] = "connection://otherConnectionX"
    os.environ["SC_TEST_VALUE"] = "branchlessValue"
    ConfigStag.load_config_file(config_path + "x123", "testImport", environment="SC_TEST_", required=False)
    assert ConfigStag.get("testImport.connections.testconnection") == "connection://otherConnectionX"
    assert ConfigStag.get("testImport.value") == "branchlessValue"
    ConfigStag.load_config_file(config_path + "x123", "", environment="SC_testImport_", required=False)
    with pytest.raises(FileNotFoundError):
        ConfigStag.load_config_file(config_path + "x123", "testImport", environment="SC_testImport_", required=True)
    os.environ["DB_NAME"] = "mydb://url"
    ConfigStag.map_environment("DB_NAME", "tests.db.name")
    assert ConfigStag.get("tests.db.name") == "mydb://url"
    ConfigStag.map_environment("DB_Name_Does_Not_Exist", "tests.db.name")
    assert ConfigStag.get("tests.db.name") == "mydb://url"
    ConfigStag.load_config_file(config_path, "", required=False)
    os.environ["SC_TESTVALUE"] = "justATest"
    ConfigStag.map_environment("SC_TESTVALUE", "testValue")
    assert ConfigStag.get("testValue") == "justATest"
    ConfigStag.get("invalidBranch.value")
    assert ConfigStag.get("invalidBranch.value", "default") == "default"


def test_dicts():
    """
    Tests dictionary setting and getting
    """
    my_dict = {"valueA": 23, "valueB": "text"}
    org_dict = copy.deepcopy(my_dict)
    ConfigStag.set("test.dictExample", my_dict)
    assert ConfigStag.get("test.dictExample") == my_dict
    my_dict["valueA"] = 24
    assert ConfigStag.get("test.dictExample")["valueA"] == 23
    assert ConfigStag.get("test.dictExample") == org_dict
