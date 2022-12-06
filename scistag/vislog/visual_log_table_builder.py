"""
Defines the class :class:`VisualLogTableBuilderExtension` and
:class:`VisualLogTableContext` which help to easily store tabular data in a
log.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Union, Callable

import numpy as np
from pandas import DataFrame, Series
from scistag.vislog.visual_log_element_context import \
    VisualLogElementContext

from scistag.imagestag import Image
from scistag.plotstag import Figure
from . import VisualLogBuilderExtension

if TYPE_CHECKING:
    from .visual_log_builder import VisualLogBuilder

ColumnContent = Union[str, int, float, Callable, Image, Figure,
                      np.ndarray, DataFrame, Series, dict, list]
"Defines the types for potential content of a column"


class VisualLogTableContext(VisualLogElementContext):
    """
    Automatically adds the beginning and ending of a table to the log
    """

    def __init__(self, builder: "VisualLogBuilder",
                 size: tuple[int, int] | None = None):
        """
        :param builder: The builder object with which we write to the log
        :param size: The table's dimensions (cols x rows) (if known in advance).

            If provided you can fill the table's contents via
            ..  code-block: python

                for row in vl.table.begin(size=(3,3)):
                    for col in row:
                        ...
        """
        self.size = size
        """
        The count of table rows and columns
        """
        log = builder.target_log
        log.write_html(f'<table class="log_table">')
        log.write_txt("\n", md=False)
        log.write_md("<table>")
        self._entered: bool = False
        "Defines if the table was entered already"
        closing_code = {"html": "</table><br>", "md": "</table><br>",
                        "txt": "\n"}
        super().__init__(builder, closing_code)

    def __enter__(self) -> VisualLogTableContext:
        if self._entered:
            return
        self._entered = True
        return self

    def __iter__(self) -> "VisualLogTableRowIterator":
        """
        Iterates through the table's rows. Requires that the table's size is
        defined. See table.begin(size=..)).

        :return: The row iterator
        """
        if self.size is None or self.size[0] is None:
            raise ValueError("Table column size not defined. Pass the size "
                             "argument to the table when creating it.")
        return self.iter_rows(self.size[1])

    def iter_rows(self, count: int) -> "VisualLogTableRowIterator":
        """
        Creates a row iterator which calls ddd_row for the count of rows
        defined.

        Usage:
        ..  code-block: python

            for row in vl.table.begin().iter_rows(8):
                ...

        :param count: Tne number of rows
        :return: The iterator object
        """
        iterator = VisualLogTableRowIterator(self, count=count)
        return iterator

    def add_row(self, content: list[ColumnContent] | None = None) \
            -> Union["VisualLogRowContext", None]:
        """
        Adds a new row context to the table.

        ..  code-block:python

            with table.add_row() as row:
                with row.add_col():
                    vl.image(...)

            table.add_row([1, 2, 3])

        :return: The row context object
        """
        if content is not None:
            self.builder.html("<tr>")
            if not isinstance(content, list):
                content = list[content]
            for element in content:
                self.builder.html("<td>")
                self.builder.add(element)
                self.builder.html("</td>")
            self.builder.html("</tr>")
            return None
        return VisualLogRowContext(self)


class VisualLogTableRowIterator:
    """
    Iterates through a set of defined rows of a VisualLogTableContext
    """

    def __init__(self, table: VisualLogTableContext, count: int):
        self.table = table
        """
        The table to which the row shall be added
        """
        self.row_count = count
        """
        The count of rows
        """
        self.index = 0
        """
        The current index
        """
        self.previous_row: VisualLogRowContext = None
        """
        The previous row (... we need to close upon starting the next element)
        """

    def __iter__(self) -> VisualLogTableRowIterator:
        """
        Returns self
        """
        return self

    def __next__(self) -> VisualLogTableRowIterator:
        """
        Starts the next row and enters it, leaves the previous one (if any)
        """
        import sys
        if self.previous_row:
            self.previous_row.__exit__(*sys.exc_info())
        if self.index >= self.row_count:
            self.table.__exit__(*sys.exc_info())
            raise StopIteration
        self.index += 1
        row = VisualLogRowContext(self.table)
        self.previous_row = row
        return row.__enter__()


class VisualLogTableColIterator:
    """
    Iterates through a set of defined rows of a VisualLogTableContext
    """

    def __init__(self, row: "VisualLogRowContext", count: int):
        self.row = row
        """
        The table to which the column shall be added
        """
        self.col_count = count
        """
        The count of rows
        """
        self.index = 0
        """
        The current index
        """
        self.previous_col: VisualLogColContext = None
        """
        The previous col (... we need to close upon starting the next element)
        """

    def __iter__(self) -> VisualLogTableColIterator:
        """
        Returns self
        """
        return self

    def __next__(self) -> VisualLogTableColIterator:
        """
        Starts the next column and enters it, leaves the previous one (if any)
        """
        import sys
        if self.previous_col:
            self.previous_col.__exit__(*sys.exc_info())
        if self.index >= self.col_count:
            raise StopIteration
        self.index += 1
        col = VisualLogColumnContext(self.row.builder)
        self.previous_col = col
        return col.__enter__()


class VisualLogRowContext(VisualLogElementContext):
    """
    Automatically adds the beginning and ending of a row to the log
    """

    def __init__(self, table: "VisualLogTableContext"):
        """
        :param builder: The builder object with which we write to the log
        """
        self.table = table
        log = self.table.builder.target_log
        log.write_html(f'<tr>\n')
        log.write_txt("| ", md=False)
        log.write_md("<tr>\n", no_break=True)
        closing_code = {"html": "</tr>", "md": "</tr>", "txt": "\n"}
        super().__init__(table.builder, closing_code)

    def __enter__(self) -> VisualLogRowContext:
        return self

    def __iter__(self):
        """
        Iterates through the row's columns. Requires that the table's size is
        defined. See table.begin(size=..)).

        :return: The column iterator
        """
        if self.table.size is None or self.table.size[0] is None:
            raise ValueError("Table column size not defined. Pass the size "
                             "argument to the table when creating it.")
        return self.iter_cols(self.table.size[0])

    def add_col(self,
                content: ColumnContent | None = None,
                md: bool = False) -> \
            Union["VisualLogColumnContext", None]:
        """
        Adds a new column to the row

        :param content: The text to be logged or the function to be called
            inside the column's context. If data is provided no context
            will be created.
        :param md: Defines if the text is markdown formatted
        :return: The column context to be entered via `with row.add_col():...`
        """
        if content is not None:
            self.builder.target_log.write_html(f"<td>")
            if isinstance(content, Callable):
                content()
            else:
                if md:
                    content = str(content)
                    self.builder.md(content)
                else:
                    self.builder.add(content)
            self.builder.target_log.write_html("</td>")
            return None

        return VisualLogColumnContext(self.builder)

    def iter_cols(self, count: int) -> "VisualLogTableColIterator":
        """
        Creates a column iterator which calls ddd_col for the count of columns
        defined.

        Usage:
        ..  code-block: python

            for row in vl.table.begin().iter_rows(8):
                for col in row.iter_cols(4):
                    ...

        :param count: Tne number of columns
        :return: The iterator object
        """
        iterator = VisualLogTableColIterator(self, count=count)
        return iterator


class VisualLogColumnContext(VisualLogElementContext):
    """
    Automatically adds the beginning and ending of a column to the log
    """

    def __init__(self, builder: "VisualLogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        log = builder.target_log
        log.write_html(f'<td>\n')
        log.write_txt("| ", md=False)
        log.write_md(f'<td>', no_break=True)
        closing_code = {"html": "</td>", "md": "</td>", "txt": " |\n"}
        super().__init__(builder, closing_code)

    def __enter__(self) -> VisualLogColumnContext:
        return self


class VisualLogTableBuilderExtension(VisualLogBuilderExtension):
    """
    Helper class for storing tables inside a log
    """

    def __init__(self, builder: VisualLogBuilder):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)
        self.show = self.__call__

    def begin(self, size: tuple[int, int] | None = None):
        """
        Creates a table logging context

        ..  code-block:

            with vl.table.begin() as table:
                for row_index in range(4):
                    with table.add_row() as row:
                        for col_index in range(4):
                            with row.add_col():
                                vl.log(col_index)

        :param size: The table's dimensions (cols x rows) (if known in advance)

            If provided you can fill the table's contents via
            ..  code-block: python

                for row in vl.table.begin(size=(3,3)):
                    for col in row:
                        ...
        :return: The logging context
        """
        return VisualLogTableContext(self.builder, size=size)

    def __call__(self, data: list[list[any]], index=False, header=False):
        """
        Adds a table to the log.

        :param data: The table data. A list of rows including a list of
            columns.

            Each row has to provide the same count of columns.

            At the moment only string content is supported.
        :param index: Defines if the table has an index column
        :param header: Defines if the table has a header
        """
        code = '<table class="log_table">\n'
        for row_index, row in enumerate(data):
            tabs = "\t"
            code += f"{tabs}<tr>\n"
            for col_index, col in enumerate(row):
                code += f"\t{tabs}<td>\n{tabs}\t"
                assert isinstance(col, str)  # more types to be supported soon
                if index and col == 0:
                    code += "<b>"
                major_cell = (row_index == 0 and header or
                              col_index == 0 and index)
                if major_cell:
                    code += f"<b>{col}</b>"
                else:
                    code += col
                if index and col == 0:
                    code += "</b>"
                code += f"\n{tabs}</td>\n"
                tabs = tabs[0:-1]
            code += f"{tabs}</tr>\n"
        code += "</table>\n"
        self.log.write_html(code)
        for row in data:
            row_text = "| "
            for index, col in enumerate(row):
                row_text += col + " | "
            self.log.write_txt(row_text, md=False)
        for row_index, row in enumerate(data):
            row_text = "| "
            for index, col in enumerate(row):
                row_text += col + " | "
            self.log.write_md(row_text)
            if row_index == 0:
                self.log.write_md("|" + "---|" * len(row))
        return self
