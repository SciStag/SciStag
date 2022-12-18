"""
Implements the :class:`CellLogger` and :class:`Cell` classes with allows the creation
of replaceable logging areas.
"""

from __future__ import annotations

from scistag.vislog import BuilderExtension, VisualLogBuilder

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.vislog.sessions.page_session import PageSession


class Cell:
    """
    The content cell defines a region within the log which can either be logged
    to surround a logical content area or for dynamic updating specific regions of
    the log.

    In HTML files it is represented with a div region.
    """

    def __init__(self, builder: VisualLogBuilder):
        self.builder = builder
        """The builder which created and owns us"""
        self.page: PageSession = self.builder.page
        """The page which stores the content"""
        self.cell_name = builder.page.reserve_unique_name("cell", 4)
        """The cell's unique name"""
        self.element = self.page.begin_sub_element(self.cell_name)
        """Defines the element which will store the cell's data"""
        self._initial = True
        """Defines if this is the initial entering turn (which will add e.g. the
        div region to the html output)"""
        self._closed = False
        """Defines if the element was closed (left) already after it was entered"""
        self.page.write_html(f'<div id="{self.cell_name}">\n')

    def enter(self) -> Cell:
        """
        Enters the region and sets it as the page's new writing target

        :return: Self
        """
        if not self._initial:
            self.page.enter_element(self.element)
            self._closed = False
        return self

    def leave(self) -> Cell:
        """
        Leaves the current cell after it was entered.

        :return Self:
        """
        if self._closed:
            return self
        self._closed = True
        if self._initial:
            self._initial = False
            self.page.end_sub_element()
            self.page.write_html(f"</div><!-- {self.cell_name} -->\n")
        else:
            self.page.end_sub_element()
        return self

    def clear(self) -> Cell:
        """
        Clears the cells content

        :return: Self
        """
        self.element.clear()
        return self

    def __enter__(self) -> Cell:
        return self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.leave()


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

    def begin(self) -> Cell:
        """
        Begins a new content cell to which you can add content with any logging
        function and can update this content at any later point in time.

        :return: The content cell reference
        """
        cell = Cell(self.builder)
        return cell

    def add(self) -> Cell:
        """
        Adds an empty content cell without filling it with content and returns it.

        :return: The content cell reference.
        """
        cell = Cell(self.builder)
        cell.leave()
        return cell
