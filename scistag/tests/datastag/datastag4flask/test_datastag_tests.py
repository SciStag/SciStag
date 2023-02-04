from scistag.tests.datastag.datastag4flask.shared_test_client import (
    test_remote_connection,
    test_client,
)
from scistag.tests.datastag.local.test_get_set import all_get_set_tests
from scistag.tests.datastag.local.test_lists import all_list_tests
from scistag.tests.datastag.local.test_deprecation import all_deprecation_tests
from scistag.tests.datastag.local.test_vault import all_common_tests
from scistag.tests.datastag.local.test_wait_for import all_async_tests


def test_original_tests(test_remote_connection):
    """
    Tests all original tests - just via Flask client now
    :param test_remote_connection: The remote connection fixture
    """
    all_get_set_tests(test_remote_connection)
    all_list_tests(test_remote_connection)
    all_deprecation_tests(test_remote_connection)
    all_common_tests(test_remote_connection)
    all_async_tests(test_remote_connection)
