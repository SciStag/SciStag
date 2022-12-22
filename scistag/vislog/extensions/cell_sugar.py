"""
Implements helper functions for the easy definition of log cells, so functions of
a VisualLogBuilder which are automatically called in the build process if they are
decorated with @cell.
"""

from __future__ import annotations

from types import MethodType, FunctionType


def cell(
    func: MethodType | FunctionType | None = None,
    interval_s: float | None = None,
    continuous: bool = False,
):
    """
    Decorates a method or function within the current VisualLogBuilder subclass or
    file as cell which will automatically be added to the log in the order of
    declaration.

    :param func: The function to be wrapped
    :param interval_s: The update interval of the cell in seconds.

        The cell will be updated at a maximum update interval either when the
        cell.invalidate() method is called or when the cell is flagged as continuous.
    :param continuous: Defines if the cell shall updated automatically with the
        interval defined.
    :return: The decorated method or function
    """

    def cell_wrapper(func_o: MethodType):
        """
        Wraps the builder method

        :param func_o: The original method
        :return: The wrapped method
        """
        func_o.__setattr__(
            "__log_cell", {"interval_s": interval_s, "continuous": continuous}
        )
        return func_o

    if func is not None:
        return cell_wrapper(func)

    return cell_wrapper
