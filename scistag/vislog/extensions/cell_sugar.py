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

CELL_ATTRIBUTE_STATIC = "static"

LOG_CELL_METHOD_FLAG = "__log_cell"


def cell(
    func: MethodType | FunctionType | None = None,
    interval_s: float | None = None,
    continuous: bool = False,
    progressive: bool = False,
    static: bool = False,
    groups: str | list[str] = None,
    uses: str | list[str] = None,
    requires: str | list[str] = None,
    tab: str | None = None,
    page: int | None = None,
    data_cell: bool = False,
):
    """
    Decorates a method or function within the current LogBuilder subclass or
    file as cell which will automatically be added to the log in the order of
    declaration.

    :param func: The function to be wrapped
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
    :param requires: A list of cache and file names which are required. Like uses
        the cell will be refreshed if the value changes but in addition the cell
        also won't be build at all before the value or file is present.
    :param groups: A list of visibility groups the page is attached to.
    :param tab: The tab in which the cell shall be displayed.
    :param page: The page index, e.g. to easily create browsable documents where
        always only one page is displayed at a time.
    :param data_cell: If set the cell will be flagged as pure data cell w/o visual
        content and thus no required updates after a rebuild.
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
                CELL_ATTRIBUTE_STATIC: static,
                "uses": uses,
                "requires": requires,
                "groups": groups,
                "tab": tab,
                "page": page,
                "data_cell": data_cell,
            },
        )
        return func_o

    if func is not None:
        return cell_wrapper(func)

    return cell_wrapper


def get_current_builder() -> Union["LogBuilder", None]:
    """
    Returns the currently active builder if one is available
    """
    from scistag.vislog import LogBuilder

    return LogBuilder.current()


cell.__dict__["vl"] = get_current_builder
