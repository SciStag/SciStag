"""
Tests the table logging helper class VisualTableLogger
"""
import sys

import pytest

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


def test_table_enumeration():
    """
    Test the basic table logging methods
    """
    vl.test.begin("Table logging via enumeration")

    with pytest.raises(ValueError):
        with vl.table.begin() as table:
            table.__enter__()
            for _ in table:
                pass
    table.__exit__(*sys.exc_info())

    with pytest.raises(ValueError):
        with vl.table.begin(size=(3, None)) as table:
            for _ in table:
                pass
    with pytest.raises(ValueError):
        with vl.table.begin(size=(None, 3)) as table:
            for row in table:
                for _ in row:
                    pass
    vl.test.checkpoint("log.table.iter")

    for row_index, row in enumerate(vl.table.begin(size=(4, 3))):
        for col_index, col in enumerate(row):
            vl.log(f"{col_index}x{row_index}")
    vl.test.assert_cp_diff(hash_val="5786dc109acba9d6672228977fca17ac")
    vl.test.checkpoint("log.table.iter_pass_size")
    for row_index, row in enumerate(vl.table.begin().iter_rows(3)):
        for col_index, col in enumerate(row.iter_cols(4)):
            vl.log(f"{col_index}x{row_index}")
    vl.test.assert_cp_diff(hash_val="5786dc109acba9d6672228977fca17ac")


def test_table_creation():
    """
    Tests the logging of table with provided data
    """
    vl.test.begin("Table logging direct")
    vl.test.checkpoint("log.table.direct")
    vl.table.show([[1, 2, 3], [4, 5, 6]], index=True)
    vl.test.assert_cp_diff(hash_val="6906d0ec9825898922bb7c577ef8aa37")

    vl.test.checkpoint("log.table.add_col")
    for row_index, row in enumerate(vl.table.begin().iter_rows(3)):
        row.add_col("123")
        row.add_col("456")
        row.add_col(lambda: vl.log.info("789"))
        row.add_col("**Markdown**", md=True)
    vl.test.assert_cp_diff(hash_val="9cf7177b040fa15e054bb5dc7f2266de")
