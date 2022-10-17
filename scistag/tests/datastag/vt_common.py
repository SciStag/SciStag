import pytest
from scistag.datastag import DataStagConnection


@pytest.fixture(scope="module")
def vault_connections():
    """
    Shared vault connection
    :return: Connecting instance to local vault
    """
    test_connection = DataStagConnection()
    connections = [test_connection]
    yield connections
    for connection in connections:
        connection.get_status(advanced=True)
