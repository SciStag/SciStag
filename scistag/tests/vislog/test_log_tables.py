"""
Tests the table logging helper class VisualTableLogger
"""

from . import vl


def test_basics_logging_methods():
    """
    Test the basic table logging methods
    """
    vl.test.begin("Table logging")
    vl.test.checkpoint("log.table.basics")
    with vl.table.begin() as table:
        with table.add_row() as row:
            for index in range(3):
                with row.add_col():
                    vl.log("Test", no_break=True)
    vl.test.assert_cp_diff(hash_val="e96df1a798a4d99488014b0d7bfb2fcc")
    vl.br()
    vl.test.checkpoint("log.table.fullrow")
    table = vl.table.begin()
    table.add_row(["1", 2, 3.0])
    table.close()
    vl.test.assert_cp_diff(hash_val="ab5f470aa9025c4dd4158c9908013662")
