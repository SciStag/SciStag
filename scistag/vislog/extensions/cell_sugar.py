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
