"""
Tests the table logging helper class VisualTableLogger
"""

from . import vl


def test_basics_logging_methods():
    """
    Test the basic table logging methods
    """
    vl.test.checkpoint()
    with vl.table.begin() as table:
        with table.add_row() as row:
            for index in range(3):
                with row.add_col():
                    vl.log("Test")
    vl.test.assert_cp_diff(hash_val="cf8404ee4e19c115d4fb342a188de7a9")
