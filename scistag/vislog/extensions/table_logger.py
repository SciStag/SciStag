"""
Defines the class :class:`TableLogger` and
:class:`TableContext` which help to easily store tabular data in a
log.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Union, Callable, Any, Literal

import numpy as np
from pandas import DataFrame, Series
from pydantic import BaseModel

from scistag.vislog.common.element_context import ElementContext

from scistag.imagestag import Image
from scistag.plotstag import Figure
from . import BuilderExtension
from ..options import LTableOptions

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import LogBuilder

ColumnContent = Union[
    str, int, float, Callable, Image, Figure, np.ndarray, DataFrame, Series, dict, list
]
"Defines the types for potential content of a column"


class TableContext(ElementContext):
    """
    Automatically adds the beginning and ending of a table to the log
    """

    def __init__(
        self,
        builder: "LogBuilder",
        size: tuple[int, int] | None = None,
        options: LTableOptions | None = None,
        html_class: str | None = None,
        seamless: bool | None = None,
        br: bool = True,
    ):
        """
        :param builder: The builder object with which we write to the log
        :param size: The table's dimensions (cols x rows) (if known in advance).

            If provided you can fill the table's contents via
            ..  code-block: python

                for row in vl.table.begin(size=(3,3)):
                    for col in row:
                        ...
        :param options: Defines the table's options
        :param html_class: The html class to be used for the table or the style code,
            see :meth:`LogBuilder.style.css`.
        :param seamless: Defines if the table shall be seamless, without visible borders
            and padding.
        :param br: Defines if the table shall be followed by a line break
        """
        linebreak_code = "<br>" if br else ""
        closing_code = {
            "html": f"</table>{linebreak_code}",
            "md": f"</table>{linebreak_code}",
            "txt": "\n" if br else "",
        }
        super().__init__(builder, closing_code)
        self.size = size
        """
        The count of table rows and columns
        """
        self.options = (
            builder.options.style.table.clone() if options is None else options
        )
        if seamless is not None:
            self.options.seamless = seamless
        if html_class is not None:
            self.options.html_class = self.builder.style.ensure_css_class(
                html_class, "vl_table_style"
            )
        table_class = self.options.get_html_class()
        html_style = self.options.html_style
        html_style = f' style="{html_style}"' if len(html_style) > 0 else ""
        self.page.write_html(f"<table class={table_class}{html_style}>")
        self.page.write_txt("\n", md=False)
        self.page.write_md(f'<table class="{table_class}"{html_style}>')
        self._entered: bool = False
        "Defines if the table was entered already"

    def __iter__(self) -> "TableRowIterator":
        """
        Iterates through the table's rows. Requires that the table's size is
        defined. See table.begin(size=..)).

        :return: The row iterator
        """
        if self.size is None or self.size[1] is None:
            raise ValueError(
                "Table column size not defined. Pass the size "
                "argument to the table when creating it."
            )
        return self.iter_rows(self.size[1])

    def iter_rows(self, count: int) -> "TableRowIterator":
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
        iterator = TableRowIterator(self, count=count)
        return iterator

    def add_row(
        self, content: list[ColumnContent] | None = None
    ) -> Union["TableRowContext", None]:
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
                content = [content]
            for element in content:
                self.builder.html("<td>")
                self.builder.add(element)
                self.builder.html("</td>")
            self.builder.html("</tr>")
            return None
        return TableRowContext(self)


class TableRowIterator:
    """
    Iterates through a set of defined rows of a TableContext
    """

    def __init__(self, table: TableContext, count: int):
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
        self.previous_row: TableRowContext | None = None
        """
        The previous row (... we need to close upon starting the next element)
        """

    def __iter__(self) -> TableRowIterator:
        """
        Returns self
        """
        return self

    def __next__(self) -> TableRowContext:
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
        row = TableRowContext(self.table)
        self.previous_row = row
        return row.__enter__()


class TableColumnIterator:
    """
    Iterates through a set of defined rows of a TableContext
    """

    def __init__(self, row: "TableRowContext", count: int):
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
        self.previous_col: TableColumnContext | None = None
        """
        The previous col (... we need to close upon starting the next element)
        """

    def __iter__(self) -> TableColumnIterator:
        """
        Returns self
        """
        return self

    def __next__(self) -> TableColumnContext:
        """
        Starts the next column and enters it, leaves the previous one (if any)
        """
        import sys

        if self.previous_col:
            self.previous_col.__exit__(*sys.exc_info())
        if self.index >= self.col_count:
            raise StopIteration
        self.index += 1
        col = TableColumnContext(self.row.builder)
        self.previous_col = col
        return col.__enter__()


class TableRowContext(ElementContext):
    """
    Automatically adds the beginning and ending of a row to the log
    """

    def __init__(self, table: "TableContext"):
        """
        :param table: The table context within which the row shall be added
        """
        closing_code = {"html": "</tr>", "md": "</tr>", "txt": "\n"}
        super().__init__(table.builder, closing_code)
        self.table = table
        self.page.write_html(f"<tr>\n")
        self.page.write_txt("| ", md=False)
        self.page.write_md("<tr>\n", no_break=True)

    def __enter__(self) -> TableRowContext:
        return self

    def __iter__(self):
        """
        Iterates through the row's columns. Requires that the table's size is
        defined. See table.begin(size=..)).

        :return: The column iterator
        """
        if self.table.size is None or self.table.size[0] is None:
            raise ValueError(
                "Table column size not defined. Pass the size "
                "argument to the table when creating it."
            )
        return self.iter_cols(self.table.size[0])

    def add_col(
        self, content: ColumnContent | None = None
    ) -> Union["TableColumnContext", None]:
        """
        Adds a new column to the row

        :param content: The text to be logged or the function to be called
            inside the column's context. If data is provided no context
            will be created.
        :return: The column context to be entered via `with row.add_col():...`
        """
        if content is not None:
            self.page.write_html(f"<td>")
            if isinstance(content, Callable):
                content()
            else:
                self.builder.add(content)
            self.page.write_html("</td>")
            return None

        return TableColumnContext(self.builder)

    def iter_cols(self, count: int) -> "TableColumnIterator":
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
        iterator = TableColumnIterator(self, count=count)
        return iterator


class TableColumnContext(ElementContext):
    """
    Automatically adds the beginning and ending of a column to the log
    """

    def __init__(self, builder: "LogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        closing_code = {"html": "</td>", "md": "</td>", "txt": " |\n"}
        super().__init__(builder, closing_code)
        self.page.write_html(f"<td>\n")
        self.page.write_txt("| ", md=False)
        self.page.write_md(f"<td>", no_break=True)

    def __enter__(self) -> TableColumnContext:
        return self


class TableLogger(BuilderExtension):
    """
    Helper class for storing tables inside a log
    """

    def __init__(self, builder: LogBuilder):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)
        self.show = self.__call__

    def begin(
        self,
        size: tuple[int, int] | None = None,
        options: LTableOptions | None = None,
        seamless: bool | None = None,
        html_class: str | None = None,
        br: bool = True,
    ):
        """
        Creates a table logging context

        ..  code-block:

            with vl.table.begin() as table:
                for row_index in range(4):
                    with table.add_row() as row:
                        for col_index in range(4):
                            with row.add_col():
                                vl.log(col_index)

            alternatively:
            with vl.table as table:
                ...

        :param size: The table's dimensions (cols x rows) (if known in advance)

            If provided you can fill the table's contents via
            ..  code-block: python

                for row in vl.table.begin(size=(3,3)):
                    for col in row:
                        ...
        :param options: Defines the table's style
        :param seamless: Defines if the table shall be seamless, without visible borders
            and padding.
        :param html_class: The html class to be used for the table or the CSS code
            to generate a new class, see :meth:`StyleContext.ensure_css_class`
        :param br: Defines if the table shall be followed by a line break
        :return: The logging context
        """
        return TableContext(
            self.builder,
            size=size,
            options=options,
            seamless=seamless,
            html_class=html_class,
            br=br,
        )

    def __call__(
        self,
        data: list[list[Any]] | list[Any],
        orientation: Literal["vert", "hor"] = "hor",
        index: bool = False,
        header: bool = False,
        options: LTableOptions | None = None,
        html_class: str | None = None,
        seamless: bool | None = None,
        br: bool = True,
    ):
        """
        Adds a table to the log.

        :param data: The table data. A list of rows including a list of
            columns.

            Each row has to provide the same count of columns.

            The data type has to be a type supported by :meth:`LogBuilder.add`.

            You can also pass a single list of values which is by default interpreted
            to be horizontal so each entry represents a column. See orientation.
        :param orientation: Defines the orientation of data passed as list,
            either "vert"ical or "hor"izontal.
        :param index: Defines if the table has an index column
        :param header: Defines if the table has a header
        :param options: Defines the table's style
        :param html_class: The html class to be used for the table or the CSS code
            to generate a new class, see :meth:`StyleContext.ensure_css_class`
        :param seamless: Defines if the table shall be seamless, without visible borders
            and padding.
        :param br: Defines if the table shall be followed by a line break
        """
        if len(data) > 0 and not isinstance(data[0], list):
            if orientation == "hor":
                data = [data]
            else:
                data = [[element] for element in data]
        row_count = len(data)
        col_count = len(data[0]) if len(data) > 0 else 0
        tc = TableContext(
            self.builder,
            size=(col_count, row_count),
            options=options,
            seamless=seamless,
            html_class=html_class,
            br=br,
        )
        with tc:
            for row_index, row in enumerate(tc):
                tabs = "\t"
                for col_index, col in enumerate(row):
                    cur_data = data[row_index][col_index]
                    if isinstance(cur_data, (str, int, float, bool)):
                        code = ""
                        if index and col_index == 0:
                            code += "<b>"
                        major_cell = (
                            row_index == 0 and header or col_index == 0 and index
                        )
                        if major_cell:
                            code += f"<b>{cur_data}</b>"
                        else:
                            code += f"{cur_data}"
                        if index and col_index == 0:
                            code += "</b>"
                        self.builder.html(code)
                    else:
                        self.builder.add(cur_data)
                    tabs = tabs[0:-1]

    def simple_table(
        self,
        data: list[list[str | int | float | bool]],
        orientation: Literal["vert", "hor"] = "hor",
        index=False,
        header=False,
        br: bool = True,
    ) -> LogBuilder:
        """
        Adds a table simple table to the log which is represented in ASCII style
        in txt and Markdown logs. It's fields may only contain simple types and it
        can not be custom styled.

        :param data: The table data. A list of rows including a list of columns.

            Each row has to provide the same count of columns.
            You can also pass a single list of values which is by default interpreted
            to be horizontal so each entry represents a column. See orientation.
        :param orientation: Defines the orientation of data passed as list,
            either "vert"ical or "hor"izontal.
        :param index: Defines if the table has an index column
        :param header: Defines if the table has a header
        :param br: Defines if the table shall be followed by a line break
        """
        if len(data) > 0 and not isinstance(data[0], list):
            if orientation == "hor":
                data = [data]
            else:
                data = [[element] for element in data]
        # html
        code = '<table class="vl_log_table">\n'
        for row_index, row in enumerate(data):
            tabs = "\t"
            code += f"{tabs}<tr>\n"
            for col_index, col in enumerate(row):
                code += f"\t{tabs}<td>\n{tabs}\t"
                assert isinstance(
                    col, (str, int, float, bool)
                )  # more types to be supported soon
                col = str(col)
                if index and col_index == 0:
                    code += "<b>"
                major_cell = row_index == 0 and header or col_index == 0 and index
                if major_cell:
                    code += f"<b>{col}</b>"
                else:
                    code += col
                if index and col_index == 0:
                    code += "</b>"
                code += f"\n{tabs}</td>\n"
                tabs = tabs[0:-1]
            code += f"{tabs}</tr>\n"
        code += "</table>\n"
        if br:
            code += "<br>"
        self.page_session.write_html(code)
        # txt
        for row in data:
            row_text = "| "
            for index, col in enumerate(row):
                col = str(col)
                row_text += col + " | "
            self.page_session.write_txt(row_text, md=False)
        # markdown
        for row_index, row in enumerate(data):
            row_text = "| "
            for index, col in enumerate(row):
                col = str(col)
                row_text += col + " | "
            self.page_session.write_md(row_text)
            if row_index == 0:
                self.page_session.write_md("|" + "---|" * len(row))
        return self.builder
