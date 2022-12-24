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
    vl.test.assert_cp_diff(hash_val="6875aa5eafa39adad739428ebbced629")
    vl.br()
    vl.test.checkpoint("log.table.fullrow")
    table = vl.table.begin()
    table.add_row(["1", 2, 3.0])
    table.close()
    vl.test.assert_cp_diff(hash_val="8b6bb47eb07f8f0a913c30bfab06ab06")


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
    vl.test.assert_cp_diff(hash_val="2293e473588af3a3ee8c7c823d1d9317")
    vl.test.checkpoint("log.table.iter_pass_size")
    for row_index, row in enumerate(vl.table.begin().iter_rows(3)):
        for col_index, col in enumerate(row.iter_cols(4)):
            vl.log(f"{col_index}x{row_index}")
    vl.test.assert_cp_diff(hash_val="2293e473588af3a3ee8c7c823d1d9317")


def test_table_creation():
    """
    Tests the logging of table with provided data
    """
    vl.test.begin("Table logging direct")
    vl.test.checkpoint("log.table.direct")
    vl.table.show([[1, 2, 3], [4, 5, 6]], index=True)
    vl.test.assert_cp_diff(hash_val="36da1036a7480739870f8fc89452d838")

    vl.test.checkpoint("log.table.add_col")
    for row_index, row in enumerate(vl.table.begin().iter_rows(3)):
        row.add_col("123")
        row.add_col("456")
        row.add_col(lambda: vl.log.info("789"))
        row.add_col("**Markdown**", md=True)
    vl.test.assert_cp_diff(hash_val="c21e7956c1f357c6a15100aceb72147f")
