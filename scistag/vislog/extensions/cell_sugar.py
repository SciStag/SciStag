"""
Implements helper functions for the easy definition of log cells, so functions of
a LogBuilder which are automatically called in the build process if they are
decorated with @cell.
"""

from __future__ import annotations

from types import MethodType, FunctionType
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.vislog import LogBuilder

LOG_CELL_METHOD_FLAG = "__log_cell"


def cell(
        func: MethodType | FunctionType | None = None,
        name: str | None = None,
        section_name: str | None = None,
        interval_s: float | None = None,
        continuous: bool = False,
        progressive: bool = False,
        static: bool = False,
        groups: str | list[str] = None,
        uses: str | list[str] = None,
        output: str | list[str] = None,
        requires: str | list[str] = None,
        tab: str | None = None,
        page: int | None = None,
        ctype: str | None = None,
):
    """
    Decorates a method or function within the current LogBuilder subclass or
    file as cell which will automatically be added to the log in the order of
    declaration.

    :param func: The function to be wrapped
    :param name: The cell's explicit name, by default the method's name will be used.
    :param section_name: The section's display text
    :param ctype: Defines the cell's type.

        Supported types are:
        - "seamless" - for a default cell w/o any decorations
        - "section" - for a cell which inserts a spacing to previous cells of the same
            type.
        - "data" - for cells which do just create data and do not need to be displayed
        - "snippet" - Defines a cell which is not displayed by itself but can be
            inserted, e.g. into inserted documents via {{SNIPPET_NAME}}

        By default "seamless" will be selected except a section title was defined.
    :param interval_s: The update interval of the cell in seconds.

        The cell will be updated at a maximum update interval either when the
        cell.invalidate() method is called or when the cell is flagged as continuous.
    :param continuous: Defines if the cell shall updated automatically with the
        interval defined.
    :param progressive: Defines if the cell is progressive and extends itself
    :param static: Defines if the cell is static. Allows producing less output html
        code but makes it impossible to modify the cell's area.
    :param uses: A list of cache and file names which shall be observed. If any of
        the elements does change the cell will be invalidated.
    :param output: A list of cache and file names this cell produces or updates
    :param requires: A list of cache and file names which are required.

        Like uses the cell will be refreshed if the value changes but in addition
        the cell  also won't be build at all before the value or file is present.

        If an element's name is extended by a >0 the element will only be rated valid
        if it has a value of greater or length greater than zero. Supported types are
        lists, floats, ints, bools, strings, bytes, numpy arrays and pandas data frames.

        See :meth:`Cache.non_zero`.
    :param groups: A list of visibility groups the page is attached to.
    :param tab: The tab in which the cell shall be displayed.
    :param page: The page index, e.g. to easily create browsable documents where
        always only one page is displayed at a time.
    :return: The decorated method or function
    """

    def cell_wrapper(func_o: MethodType):
        """
        Wraps the builder method

        :param func_o: The original method
        :return: The wrapped method
        """
        if not isinstance(func_o, FunctionType) or isinstance(func_o, MethodType):
            raise ValueError("Only functions and methods can be defined as log cells")
        func_o.__setattr__(
            LOG_CELL_METHOD_FLAG,
            {
                "interval_s": interval_s,
                "continuous": continuous,
                "progressive": progressive,
                "name": name,
                "section": section_name,
                "static": static,
                "uses": uses,
                "output": output,
                "requires": requires,
                "groups": groups,
                "tab": tab,
                "page": page,
                "ctype": ctype,
            },
        )
        return func_o

    if func is not None:
        return cell_wrapper(func)

    return cell_wrapper


def data(
        *args,
        name: str | None = None,
        interval_s: float | None = None,
        continuous: bool = False,
        uses: str | list[str] = None,
        output: str | list[str] = None,
        requires: str | list[str] = None,
        **kwargs,
):
    """
    Defines a data cell which can be used to load or produce initial data.

    It can not contain visual content by itself and does not trigger any client side
    view updates.

    :param name: The cell's explicit name, by default the method's name will be used.
    :param interval_s: The update interval of the cell in seconds.

        The cell will be updated at a maximum update interval either when the
        cell.invalidate() method is called or when the cell is flagged as continuous.
    :param continuous: Defines if the cell shall updated automatically with the
        interval defined.
    :param uses: A list of cache and file names which shall be observed. If any of
        the elements does change the cell will be invalidated.
    :param output: A list of cache and file names this cell produces or updates
    :param requires: A list of cache and file names which are required.
    :param args: Further positional arguments
    :param kwargs: Further keyword arguments. See :class:`Cell`
    :return: The wrapped method
    """
    return cell(
        *args,
        ctype="data",
        name=name,
        interval_s=interval_s,
        continuous=continuous,
        uses=uses,
        output=output,
        requires=requires,
        **kwargs,
    )


def processing(
        *args,
        name: str | None = None,
        interval_s: float | None = None,
        continuous: bool = False,
        uses: str | list[str] = None,
        output: str | list[str] = None,
        requires: str | list[str] = None,
        **kwargs,
):
    """
    Defines a data cell which is ment for processing data, e.g. provided through an
    event.

    It can not contain visual content by itself and does not trigger any client side
    view updates.

    :param name: The cell's explicit name, by default the method's name will be used.
    :param interval_s: The update interval of the cell in seconds.

        The cell will be updated at a maximum update interval either when the
        cell.invalidate() method is called or when the cell is flagged as continuous.
    :param continuous: Defines if the cell shall updated automatically with the
        interval defined.
    :param uses: A list of cache and file names which shall be observed. If any of
        the elements does change the cell will be invalidated.
    :param output: A list of cache and file names this cell produces or updates
    :param requires: A list of cache and file names which are required.
    :param args: Further positional arguments
    :param kwargs: Further keyword arguments. See :class:`Cell`
    :return: The wrapped method
    """
    return cell(
        *args,
        ctype="processing",
        name=name,
        interval_s=interval_s,
        continuous=continuous,
        uses=uses,
        output=output,
        requires=requires,
        **kwargs,
    )


def section(
        *args,
        title: str | None = None,
        name: str | None = None,
        interval_s: float | None = None,
        continuous: bool = False,
        uses: str | list[str] = None,
        output: str | list[str] = None,
        requires: str | list[str] = None,
        **kwargs,
):
    """
    Defines a data cell which can be used to load or produce initial data.

    It can not contain visual content by itself and does not trigger any client side
    view updates.

    :param title: The section's title
    :param name: The cell's explicit name, by default the method's name will be used.
    :param interval_s: The update interval of the cell in seconds.

        The cell will be updated at a maximum update interval either when the
        cell.invalidate() method is called or when the cell is flagged as continuous.
    :param continuous: Defines if the cell shall updated automatically with the
        interval defined.
    :param uses: A list of cache and file names which shall be observed. If any of
        the elements does change the cell will be invalidated.
    :param output: A list of cache and file names this cell produces or updates
    :param requires: A list of cache and file names which are required.
    :param args: Further positional arguments
    :param kwargs: Further keyword arguments. See :class:`Cell`
    :return: The wrapped method
    """
    if len(args) and isinstance(args[0], str):
        title = args[0]
        args = args[1:]
    return cell(
        *args,
        section_name=title,
        ctype="section",
        name=name,
        interval_s=interval_s,
        continuous=continuous,
        uses=uses,
        output=output,
        requires=requires,
        **kwargs,
    )


def once(
        *args,
        name: str | None = None,
        uses: str | list[str] = None,
        requires: str | list[str] = None,
        output: str | list[str] = None,
        **kwargs,
):
    """
    Defines a data cell which can be used to load or produce initial data.

    It is guaranteed to only be called once, regardless even of total refreshes of
    the whole log.

    It can not contain visual content by itself and does not trigger any client side
    view updates.

    :param name: The cell's explicit name, by default the method's name will be used.
    :param uses: A list of cache and file names which shall be observed. If any of
        the elements does change the cell will be invalidated.
    :param requires: A list of cache and file names which are required.
    :param output: A list of cache and file names this cell produces or updates
    :param args: Further positional arguments
    :param kwargs: Further keyword arguments. See :class:`Cell`
    :return: The wrapped method
    """
    if kwargs.get("continuous", None) is not None:
        raise ValueError("A cell flagged as once will only get executed once. "
                         "continuous does not make sense and is forbidden.")
    if kwargs.get("interval_s", None) is not None:
        raise ValueError("A cell flagged as once will only get executed once. "
                         "interval_s does not make sense and is forbidden.")
    return cell(
        *args,
        ctype="once",
        name=name,
        uses=uses,
        output=output,
        requires=requires,
        **kwargs,
    )


def get_current_builder() -> Union["LogBuilder", None]:
    """
    Returns the currently active builder if one is available
    """
    from scistag.vislog import LogBuilder

    return LogBuilder.current()


cell.__dict__["vl"] = get_current_builder
