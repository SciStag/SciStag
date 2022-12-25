"""
Implements the :class:`CellLogger` and :class:`Cell` classes with allows the creation
of replaceable logging areas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union, Callable

from scistag.vislog import BuilderExtension, VisualLogBuilder
from scistag.vislog.widgets.cell import Cell

if TYPE_CHECKING:
    from scistag.vislog.widgets.cell import CellOnBuildCallback


class CellLogger(BuilderExtension):
    """
    The cell logger adds a content cell to the log similar to a code cell in Jupyter
    Notebook.

    A very practical usage scenario with this is that you can keep a reference to a
    cell and update it's content at any later point in time, e.g. using sliders
    to update diagrams.
    """

    def __init__(self, builder: VisualLogBuilder):
        """
        :param builder: The builder we are using to write to the log
        """
        super().__init__(builder)
        self.cells: dict[str, Cell] = {}
        """
        Dictionary of all registered cells
        """

    def begin(
        self,
        progressive: bool = False,
        interval_s: float | None = None,
        continuous: bool = False,
    ) -> Cell:
        """
        Begins a new content cell to which you can add content with any logging
        function and can update this content at any later point in time.

        :param progressive: Defines if the cell shall be updated progressively.

            Data will be visible as soon as the line was executed rather than at
            the end of the cell's build function.
        :param interval_s: The update interval of the cell in seconds.

            The cell will be updated at a maximum update interval either when the
            cell.invalidate() method is called or when the cell is flagged as
            continuous.
        :param continuous: Defines if the cell shall updated automatically with the
            interval defined.
        :return: The content cell reference
        """
        cell = Cell(
            builder=self.builder,
            progressive=progressive,
            interval_s=interval_s,
            continuous=continuous,
        )
        return cell

    def add(
        self,
        progressive: bool = False,
        interval_s: float | None = None,
        continuous: bool = False,
        on_build: Union["CellOnBuildCallback", None] = None,
        _builder_method: Union[Callable, None] = None,
    ) -> Cell:
        """
        Adds an empty content cell without filling it with content and returns it.

        :param progressive: Defines if the cell shall be updated progressively.

            Data will be visible as soon as the line was executed rather than at
            the end of the cell's build function.
        :param interval_s: The update interval of the cell in seconds.

            The cell will be updated at a maximum update interval either when the
            cell.invalidate() method is called or when the cell is flagged as
            continuous.
        :param continuous: Defines if the cell shall updated automatically with the
            interval defined.
        :param on_build: The method to be called when ever the cell was invalidated
            or if the update mode is set to continuous.
        :param _builder_method: The object method to which this cell is attached
        :return: The content cell reference.
        """
        cell = Cell(
            builder=self.builder,
            progressive=progressive,
            interval_s=interval_s,
            continuous=continuous,
            on_build=on_build,
            _builder_method=_builder_method,
        )
        cell.leave()
        return cell

    def __setitem__(self, key: str, value: Cell):
        """
        Registers a cell so it can be accessed by other functions

        :param key: The cell's name
        :param value: The cell
        """
        self.cells[key] = value

    def __getitem__(self, item) -> Cell:
        """
        Returns a registered cell

        :param item: The cell's name
        :return: The Cell object
        """
        return self.cells[item]

    def __len__(self):
        """
        Returns the count of registered cells
        """
        return len(self.cells)

    def __contains__(self, item):
        """
        Returns if a cell with given name does exist
        """
        return item in self.cells
