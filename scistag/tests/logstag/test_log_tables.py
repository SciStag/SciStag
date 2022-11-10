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
    vl.test.assert_cp_diff(hash_val="c65297e443337509638d95c9d0e83450")

    vl.test.checkpoint()
    table = vl.table.begin()
    table.add_row(["1", 2, 3.0])
    table.close()
    vl.test.assert_cp_diff(hash_val="e702a05e36c465ebccb29268f5cdf8bc")
