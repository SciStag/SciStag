"""
Tests the table logging helper class VisualTableLogger
"""
import sys

import pytest

from . import vl
from ...vislog import MDCode, VisualLog
from ...vislog.options import LogTableOptions


def test_basics_logging_methods():
    """
    Test the basic table logging methods
    """
    vl.test.begin("Table logging")
    vl.test.checkpoint("log.table.basics")
    with vl.table.begin() as table:
        with table.add_row() as row:
            for index in range(3):
                with row.add():
                    vl.add("Test")
    vl.test.assert_cp_diff(hash_val="be9196e509966b47580c4bd9e227d564")
    vl.br()
    vl.test.checkpoint("log.table.fullrow")
    table = vl.table.begin()
    table.add_row(["1", 2, 3.0])
    table.close()
    vl.test.assert_cp_diff(hash_val="87a7f613e560d0516dca6e09609022c6")


def test_table_enumeration():
    """
    Test the basic table logging methods
    """
    vl.test.begin("Table logging via enumeration")

    vl.test.checkpoint("log.table.iter")

    for row_index, row in enumerate(vl.table.begin(size=(4, 3))):
        for col_index, col in enumerate(row):
            vl.log(f"{col_index}x{row_index}")
    vl.test.assert_cp_diff(hash_val="3b3fa764760c91fec5f98f571a96d686")
    vl.test.checkpoint("log.table.iter_pass_size")
    for row_index, row in enumerate(vl.table.begin().iter_rows(3)):
        for col_index, col in enumerate(row.iter_cols(4)):
            vl.log(f"{col_index}x{row_index}")
    vl.test.assert_cp_diff(hash_val="3b3fa764760c91fec5f98f571a96d686")

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


def test_table_creation():
    """
    Tests the logging of table with provided data
    """
    vl.test.begin("Table logging direct")
    vl.test.checkpoint("log.table.direct")
    vl.table.show([[1, 2, 3], [4, 5, 6]], index=True)
    vl.test.assert_cp_diff(hash_val="edcd6ae9f7a4ebb3cbb93bace909f89b")

    vl.test.checkpoint("log.table.add_col")
    for row_index, row in enumerate(vl.table.begin().iter_rows(3)):
        row.add("123")
        row.add("456")
        row.add(lambda: vl.log.info("789"))
        row.add(MDCode("**Markdown**"))
    vl.test.assert_cp_diff(hash_val="df45cd803447d8f325532f293465310a")


def test_content_logging():
    """
    Tests the logging of content directly provided to the table function to the log
    """
    vl.test.checkpoint("table_logging")
    with vl.table.begin() as table:
        table.add_row(123)
        table.add_row([456, 789])

    vl.table([123, 456])  # log a horizontal, single row table
    vl.table([123, 456], orientation="ver")  # log a vertical, single column table
    vl.table.simple_table([[123, 456], [789, "123"], [45.678, True]], header=True)
    vl.table.simple_table([123, 456])  # single, horizontal
    vl.table.simple_table([456.78, 910], orientation="ver", br=False, index=True)
    # single, vertical
    vl.test.assert_cp_diff("2017bb6d161a2a7569b30358e5e15c1e")


def test_custom_class():
    """
    Tests using custom class and styles

    :return:
    """
    options = LogTableOptions()

    temp_log = VisualLog(fixed_session_id="")
    temp_log.default_builder.test.checkpoint("custom_css_table")

    with temp_log.default_builder.table.begin(
        options=options,
        html_class="table.{{C}} td {border: 1px solid red; padding: 40px}",
    ) as table:
        table.add_row(["Test", "Test2"])
        table.add_row(["Test3", "Test4"])

    temp_log.default_builder.test.assert_cp_diff("d4eaa5be8ee7cedd6996c624ff13f6aa")

    backup = temp_log.default_builder.create_backup()
    vl.insert_backup(backup)
