"""
Provides Flask access for tess
"""

from unittest import mock
import pytest
from flask import Flask
from scistag.datastag4flask.data_stag_blueprint import data_stag_service
from scistag.datastag.data_stag_connection import DataStagConnection


def setup_server():
    server = Flask(__name__)
    server.register_blueprint(data_stag_service)
    return server


@pytest.fixture(scope='module')
def test_client():
    """
    Creates a Flask server and returns a client to access it and test it's functions
    :return: The test client
    """
    flask_app = setup_server()
    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            yield testing_client  # this is where the testing happens!

@pytest.fixture(scope='module')
def test_remote_connection(test_client):
    """
    Returns a flask test client and returns a DataStagConnection pointing to this test client
    :param test_client: The test client
    :return: The data stag connection
    """
    connection = DataStagConnection(local=False, _request_client=test_client)
    yield connection
