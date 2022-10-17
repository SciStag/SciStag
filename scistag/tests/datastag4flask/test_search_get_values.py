from scistag.tests.datastag4flask.shared_test_client import test_client, test_remote_connection


def test_find_get_values(test_remote_connection):
    trc = test_remote_connection
    assert trc.set("some.branch.testA", 123)
    assert trc.set("some.branch.xTestB", "456")
    assert trc.set("some.branch.xTestC", True)
    # find
    values = trc.find("some.branch.*")
    assert "some.branch.testA" in values and "some.branch.xTestB" in values and "some.branch.xTestC" in values
    values = trc.find("some.branch.x*")
    assert "some.branch.testA" not in values and "some.branch.xTestB" in values and "some.branch.xTestC" in values
    values = trc.find("some.branch.*", relative_names=True)
    assert "testA" in values and "xTestB" in values and "xTestC" in values
    values = trc.get_values_by_name("some.branch.*", flat=True)
    assert 123 in values and "456" and True in values
    values = trc.get_values_by_name("some.branch.*", flat=False)
    names = [element['name'] for element in values]
    data = [element['value'] for element in values]
    assert "some.branch.testA" in names and "some.branch.xTestB" in names and "some.branch.xTestC" in names
    assert 123 in data and "456" in data and True in data
