"""
Defines the class :class:`VisualLogTableLogger` which helps storing tabular
data in a log.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Union, Callable

import numpy as np
from pandas import DataFrame, Series
from scistag.logstag.vislog.visual_log_element_context import \
    VisualLogElementContext

from scistag.imagestag import Image
from scistag.plotstag import Figure

if TYPE_CHECKING:
    from .visual_log_builder import VisualLogBuilder

ColumnContent = Union[str, int, float, Callable, Image, Figure,
                      np.ndarray, DataFrame, Series, dict, list]
"Defines the types for potential content of a column"


class VisualLogTableContext(VisualLogElementContext):
    """
    Automatically adds the beginning and ending of a table to the log
    """

    def __init__(self, builder: "VisualLogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        log = builder.target_log
        log.write_html(f'<table class="log_table">')
        log.write_txt("\n", md=True)
        closing_code = {"html": "</table><br>", "md": "\n", "txt": "\n"}
        super().__init__(builder, closing_code)

    def __enter__(self) -> VisualLogTableContext:
        return self

    def add_row(self, content: list[ColumnContent] | None = None) \
            -> "VisualLogRowContext":
        """
        Adds a new row context to the table.

        ..  code-block:python

            with table.add_row() as row:
                with row.add_col():
                    vl.image(...)

            table.add_row([1, 2, 3])

        :return: The row context object
        """
        return VisualLogRowContext(self.builder)


class VisualLogRowContext(VisualLogElementContext):
    """
    Automatically adds the beginning and ending of a row to the log
    """

    def __init__(self, builder: "VisualLogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        log = builder.target_log
        log.write_html(f'<tr>\n')
        log.write_txt("| ", md=True)
        closing_code = {"html": "</tr>", "md": "\n", "txt": "\n"}
        super().__init__(builder, closing_code)

    def __enter__(self) -> VisualLogRowContext:
        return self

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
        log.write_txt("| ", md=True)
        closing_code = {"html": "</td>", "md": " |\n", "txt": " |\n"}
        super().__init__(builder, closing_code)

    def __enter__(self) -> VisualLogColumnContext:
        return self


class VisualLogTableLogger:
    """
    Helper class for storing tables inside a log
    """

    def __init__(self, builder: "VisualLogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        self.show = self.__call__
        self.builder: "VisualLogBuilder" = builder
        self.log = self.builder.target_log

    def begin(self):
        """
        Creates a table logging context

        ..  code-block:

            with vl.table.begin() as table:
                for row_index in range(4):
                    with table.add_row() as row:
                        for col_index in range(4):
                            with row.add_col():
                                vl.log(col_index)

        :return: The logging context
        """
        return VisualLogTableContext(self.builder)

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
            self.log.write_txt(row_text, md=True)
        return self
