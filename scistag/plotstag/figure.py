"""
Defines the :class:`Figure` and all it's helper classes which lay the foundation
for rendering plots.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from enum import Enum
from math import ceil
from typing import Any

import numpy as np

from scistag.imagestag import Size2D, Colors, Canvas, Image, Pos2D
from scistag.imagestag.size2d import Size2DTypes
from scistag.imagestag.font import Font
from scistag.imagestag.font_registry import FontRegistry
from scistag.plotstag import Plot

if TYPE_CHECKING:
    from .layers.matplot_layer import MPLayerLock

FIGURE_DEFAULT_BORDER_COLOR = Colors.BLACK
"Defines the figure's default border color"

FIGURE_DEFAULT_BORDER_WITH = 1.0
"Defines the figure's default border with (at 96 DPI)"

FIGURE_DEFAULT_BORDER_MARGIN = 8.0
"The default border margin for figures"

FIGURE_DEFAULT_PLOT_SPACING = 8.0
"The default spacing between plots in a grid"

MIN_CELL_SIZE = 16
"Defines the minimum size of a plot cell if not further specified"


class GridSteppingMode(Enum):
    """
    Defines the stepping movement on the figure's grid when iterating through
    the single grids.
    """

    RIGHT_DOWN = 0
    """
    Move column-wise to the right and then row-wise downwards, like on a 
    typewriter
    """
    RIGHT_UP = 1
    "Move column-wise from left to the right and the upwards"
    LEFT_DOWN = 2
    "Move column-wise from right to the left and then downwards"
    LEFT_UP = 3
    "Move column-wise from right to left and then upwards"
    DOWN_RIGHT = 4
    "Move down row-wise first and then to the right from the upper left"
    DOWN_LEFT = 5
    "Move down row-wise first and then to the left from the upper right"
    UP_RIGHT = 6
    "Move up row-wise first and then to the right from the bottom left"
    UP_LEFT = 7
    "Move up row-wise first and then to the left from the bottom right"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        class Definitions:
            short_codes = {
                "rd": cls.RIGHT_DOWN,
                "ru": cls.RIGHT_UP,
                "ld": cls.LEFT_DOWN,
                "lu": cls.LEFT_UP,
                "dr": cls.DOWN_RIGHT,
                "dl": cls.DOWN_LEFT,
                "ur": cls.UP_RIGHT,
                "ul": cls.UP_LEFT,
                "rightDown": cls.RIGHT_DOWN,
                "rightUp": cls.RIGHT_UP,
                "leftDown": cls.LEFT_DOWN,
                "leftUp": cls.LEFT_UP,
                "downRight": cls.DOWN_RIGHT,
                "downLeft": cls.DOWN_LEFT,
                "upRight": cls.UP_RIGHT,
                "upLeft": cls.UP_LEFT,
            }

        if value in Definitions.short_codes:
            return Definitions.short_codes[value]
        return None

    def get_movement(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """
        Returns the movement order for this setting

        :return: The movement order (first step, break step direction on the
            x, y axes)
        """

        class MovementDefinitions:
            grid_stepping_movement = {
                GridSteppingMode.RIGHT_DOWN: ((+1, 0), (0, +1)),
                GridSteppingMode.RIGHT_UP: ((+1, 0), (0, -1)),
                GridSteppingMode.LEFT_DOWN: ((-1, 0), (0, +1)),
                GridSteppingMode.LEFT_UP: ((-1, 0), (0, -1)),
                GridSteppingMode.DOWN_RIGHT: ((0, +1), (+1, 0)),
                GridSteppingMode.DOWN_LEFT: ((0, +1), (-1, 0)),
                GridSteppingMode.UP_RIGHT: ((0, -1), (+1, 0)),
                GridSteppingMode.UP_LEFT: ((0, -1), (-1, 0)),
            }
            "Defines the movement of the stepping along a grid in given mode"

        return MovementDefinitions.grid_stepping_movement[self]


class FigureGridIterator:
    """
    Iterator for iterating through a figure's grid.

    The plot element contains the iteration index and the column and row.
    """

    def __init__(self, figure: "Figure"):
        """
        :param figure: The figure through which we iterate
        """
        self.index = 0
        self.figure = figure

    def __next__(self) -> Plot:
        """
        :return: Returns the next plot
        """
        col, row = self.figure.get_location(self.index)
        if col is None:
            raise StopIteration
        self.index += 1
        return self.figure.add_plot(col, row)


class Figure:
    """
    Defines a canvas onto which one or multiple :class:`Plot`s may be printed,
    manages their appearance, their behavior and different methods
    to rasterize or export plots.
    """

    def __init__(
        self,
        cols: int | None = 1,
        rows: int = 1,
        dims: tuple[int | None, int | None] | None = None,
        size: Size2DTypes | None = None,
        count: int | None = None,
        plot_size: tuple[float, float] | None = None,
        scaling: float = 1.0,
        stepping: GridSteppingMode | str = "rightDown",
        borderless: bool = False,
    ):
        """
        :param rows: The number of rows
        :param cols: The number of columns
        :param dims: The count of columns and rows as tuple.
            Overwrites rows and columns if provided.

            Examples:
        :param size: The (precise) target size in pixels.

            Great for plotting diagrams etc. with precise size, not well
            suited for images and matrices. Prefer plot_default_size for
            such data types.
        :param count: If specified it will automatically adjust the row
            count to be able to store all elements.
            If columns is explicitly set to None it will adjust the column
            count instead.
        :param plot_size: The area provided per plot if no other size
            is enforced. Adapts better to the size of images and matrices.
        :param scaling: The figure's DPI based scaling factor (1.0 = 96 DPI)
        :param stepping: Defines the mode and order in which the
            cursor iterates through the figure when using
            ``for plot in figure``. See :class:`GridSteppingMode`

            Also allows short-codes such as "rightDown", "rd" or "downRight"
            as defined in :class:`GridSteppingMode`.
        :param borderless: If set to true by default all borders and margins
            will be removed for the figure and all plots.
        """
        self.size = size
        """
        Defines the figure's efficient size in pixels (as far as known in the
        current state)
        """
        if dims is not None:
            cols = dims[0] if dims[0] is not None else cols
            rows = dims[1] if dims[1] is not None else rows
        self.scaling = scaling
        """
        The figure's scaling factor
        """
        self.background_color = Colors.WHITE
        "The figure's background color"
        self.target_size = Size2D(size) if size is not None else None
        """
        Defines the target size of the figure in pixels. If not defined the
        figure will automatically adapt to the plots' optimal size
        """
        if count is not None:
            if cols is None:
                cols = int(ceil(count / rows))
            else:
                rows = int(ceil(count / cols))
        if cols < 1 or rows < 1:
            raise ValueError("Invalid figure size")
        self.column_count = cols
        "The count of plots in a row"
        self.row_count = rows
        "The count of plots in a column"
        self.plots: dict[tuple[int, int] : Plot] = {}
        "Dictionary of the defined plots"
        self.border_margins = [FIGURE_DEFAULT_BORDER_MARGIN] * 4
        "The border margin in pixels"
        self.border_width = FIGURE_DEFAULT_BORDER_WITH
        "The border width in pixels"
        self.border_color = FIGURE_DEFAULT_BORDER_COLOR
        "The border color"
        self.default_plot_border_width: int | None = None
        """
        The default border size for plots. If not defined the default size
        will be used
        """
        self.default_plot_border_margin_size: int | None = None
        """
        Defines the base margin between a plot's border and it's content.
        If not defined the default size will be used.
        """
        self.margins = [margin for margin in self.border_margins]
        """
        The margin around the main layers in pixels on each side
        (left, top, right, bottom)
        """
        if plot_size is None:
            plot_size = tuple(np.array([512.0, 512.0]) * scaling)
        self.plot_default_size = Size2D(plot_size)
        """
        The default size per plot in pixels if no other sizes are enforced.
        """
        self.grid_spacing = Size2D(
            FIGURE_DEFAULT_PLOT_SPACING, FIGURE_DEFAULT_PLOT_SPACING
        )
        "The horizontal and vertical spacing between two plots on the grid"
        self._col_widths: list[float] = []
        "The width of each column in pixels"
        self._row_heights: list[float] = []
        "The height of each row in pixels"
        if isinstance(stepping, str):
            stepping = GridSteppingMode(stepping)
        self._iteration_stepping: GridSteppingMode = stepping
        "The movement of the cursor when iterating the grid"
        self._stepping_dict: dict[tuple[int, int], int] = {
            self.get_location(index): index
            for index in range(self.column_count * self.row_count)
        }
        "Back conversion dictionary from location to index"
        # outer margin
        self._total_margin_width = 0.0
        "Total margin width"
        self._total_margin_height = 0.0
        "Total margin height"
        self._total_hor_spacing = 0.0
        "Total space for horizontal space between grids"
        self._total_vert_spacing = 0.0
        "Total space for vertical space between grids"
        self._blocked_space = (0.0, 0.0)
        "The total amount of blocked space through border, margin etc."
        self.default_font = "Roboto"
        "The default font for all elements"
        self.default_figure_title_size = int(round(22 * scaling))
        "The default font size of figure titles"
        self.default_plot_title_size = int(round(18 * scaling))
        "The default font size of plot titles"
        self.default_plot_title_spacing = (
            int(round(2 * scaling)),
            int(round(2 * scaling)),
        )
        "The space below and above a plot's title"
        self.default_figure_title_spacing = (
            int(round(6 * scaling)),
            int(round(0 * scaling)),
        )
        "The space below and above a figure's title"
        self.title = None
        "The plot's title"
        self.title_height = 0.0
        "The title's size in pixels"
        self._title_font: Font | None = None
        "Cached title font"
        self.title_spacing: tuple[float, float] = (0.0, 0.0)
        "Space above and below the title"
        self.title_color = Colors.BLACK
        "The title's color"
        self._update_blocked_space()

    def _repr_png_(self) -> bytes:
        """
        Returns the IPython PNG representation

        :return: PNG data as bytes
        """
        return self.render().to_png()

    def set_title(self, title: str | None) -> Figure:
        """
        Sets the plot's title

        :param title: The plot's title text. None do deactivate the title
        :return: The plot
        """
        self.title = title
        if self.title is None:
            self.title_height = 0.0
            return self
        self.title_spacing = self.default_figure_title_spacing
        self._title_font = FontRegistry.get_font(
            self.default_font, size=self.default_figure_title_size
        )
        "The title's size in pixels"
        text_size = self._title_font.get_text_size(title)
        self.title_height = (
            text_size.height + self.title_spacing[0] + self.title_spacing[1]
        )
        self.update_layouts()
        return self

    def update_margins(self):
        """
        Updates the figure's margins
        """
        self.margins = [margin for margin in self.border_margins]
        self.margins[1] += self.title_height

    def set_stepping_mode(self, mode: GridSteppingMode):
        """
        Changes the behavior in which order the single grids of this figure
        are iterated and indexed. By default the cursor moves from left ro
        right and then continues in the next row.

        With other modes you can for example fill the grid in a different
        order, e.g. from to to bottom, see :class:`GridSteppingMode`.

        :param mode: The new mode
        """
        if mode == self._iteration_stepping:
            return
        self._iteration_stepping = mode
        self._stepping_dict = {
            self.get_location(index): index
            for index in range(self.column_count * self.row_count)
        }

    def __iter__(self) -> FigureGridIterator:
        """
        Creates an iterator to fill the grid with an easy for loop

        :return: The iterator
        """
        return FigureGridIterator(self)

    def set_plot(self, plot: Plot, column: int = 0, row: int = 0):
        """
        Updates a plot ot a specific index.

        If not index is specified it will define the main plot (0,0).

        :param plot: The plot to be assigned to given column and row index
        :param column: The plot's column
        :param row: The plot's row
        :return:
        """
        if (
            column < 0
            or column >= self.column_count
            or row < 0
            or row >= self.row_count
        ):
            raise IndexError("Column or row out of range")
        self.plots[(column, row)] = plot
        plot.column = column
        plot.row = row
        plot.index = self._stepping_dict[(column, row)]
        plot.set_figure(self)

    def add_plot(self, col: int = 0, row: int = 0) -> Plot:
        """
        Adds an empty plot at given location.

        If a plot was already assigned the existing plot will be returned.

        :param col: The plot's column
        :param row: The plot's row
        :return: The plot
        """
        if (col, row) in self.plots:
            plot = self.plots[(col, row)]
            plot.column = col
            plot.row = row
            plot.index = self._stepping_dict[(col, row)]
            return plot
        plot = Plot()
        self.set_plot(plot, col, row)
        return plot

    def get_location(self, enum_index: int) -> tuple[int | None, int | None]:
        """
        Returns the location of given grid by enumeration index.

        Note: In which order the grids are processed is defined by
        :attr:`iteration_stepping` so index 0 is not necessarily 0, 0 but
        e.g. in a stepping from the upper left corner could also start
        at 0, row_count-1.

        :param enum_index: The enumeration index (from 0 .. col*row -1)
        :return: The column and row of the grid, None if index is out of range
        """
        if enum_index >= self.column_count * self.row_count:
            return None, None
        its = self._iteration_stepping.get_movement()
        upwards = its[0][1] == -1 or its[1][1] == -1
        left = its[0][0] == -1 or its[1][0] == -1
        column_wise = its[0][0] != 0
        start_x = self.column_count - 1 if left else 0
        start_y = self.row_count - 1 if upwards else 0
        if column_wise:
            rows_done = enum_index // self.column_count
            col_rest = enum_index % self.column_count
            return (start_x + col_rest * its[0][0], start_y + rows_done * its[1][1])
        else:
            cols_done = enum_index // self.row_count
            row_rest = enum_index % self.row_count
            return (start_x + cols_done * its[1][0], start_y + row_rest * its[0][1])

    def update_layouts(self):
        """
        Updates the layouting of all plots and the own size
        """
        self.update_margins()
        self._update_blocked_space()

        # update percentual, desired size of one is defined
        if self.target_size is not None:
            for element in self.plots.values():
                element: Plot
                size = self._get_target_plot_size()
                element.target_size = size
        for element in self.plots.values():
            element: Plot
            element.update_layout()
        # compute the effective size
        col_widths, row_heights = self._determine_col_row_sizes()
        self._col_widths = col_widths
        "Column widths in pixels"
        self._row_heights = row_heights
        "Row heights in pixels"
        # combine
        total_width = float(np.sum(self._col_widths)) + self._blocked_space[0]
        total_height = float(np.sum(self._row_heights)) + self._blocked_space[1]
        self.size = Size2D(round(total_width), round(total_height))
        "Own size in pixels"

    def _update_blocked_space(self):
        """
        Updates the blocked space computation to determine how much space is
        available for the plots
        """
        # outer margin
        self._total_margin_width = self.margins[0] + self.margins[2]
        self._total_margin_height = self.margins[1] + self.margins[3]
        # spacing between grids
        self._total_hor_spacing = (self.column_count - 1) * self.grid_spacing.width
        self._total_vert_spacing = (self.row_count - 1) * self.grid_spacing.height
        self._blocked_space = (
            self._total_margin_width + self._total_hor_spacing,
            self._total_margin_height + self._total_vert_spacing,
        )

    def _determine_col_row_sizes(self) -> tuple[list[float], list[float]]:
        """
        Determines the efficient size of all plots
        :return: The width of the single columns and the height of the single
            rows.
        """
        row_heights: list[float] = []
        col_widths: list[float] = []
        for col in range(self.column_count):  # determine column widths
            cur_col_width = MIN_CELL_SIZE
            for key, value in self.plots.items():
                value: Plot
                size = value.size if value.target_size is None else value.target_size
                if key[0] == col and size.width > cur_col_width:
                    cur_col_width = size.width
            col_widths.append(round(cur_col_width))
        for row in range(self.row_count):  # determine row heights
            cur_row_height = MIN_CELL_SIZE
            for key, value in self.plots.items():
                value: Plot
                size = value.size if value.target_size is None else value.target_size
                if key[1] == row and size.height > cur_row_height:
                    cur_row_height = size.height
            row_heights.append(round(cur_row_height))
        return col_widths, row_heights

    def _get_target_plot_size(self) -> Size2D | None:
        """
        Returns the target size of the defined plot
        (if a target size was defined).

        :return: The size in pixels
        """
        if self.target_size is None:
            return None
        remaining_size = (
            max(self.target_size.width - self._blocked_space[0], 0),
            max(self.target_size.height - self._blocked_space[1], 0),
        )
        return Size2D(
            remaining_size[0] / self.column_count, remaining_size[1] / self.row_count
        )

    def render(self) -> Image:
        """
        Renders the figure and returns it as image

        :return: The visualization of the plot as :class:`Image`
        """
        self.update_layouts()
        size = self.size.to_int_tuple()
        canvas = Canvas(size=size, default_color=self.background_color)
        if self.border_width != 0.0:  # frame
            canvas.rect(
                pos=(0, 0),
                size=size,
                outline_color=self.border_color,
                outline_width=int(round(self.border_width)),
            )
        if self.title is not None:
            text_size = self._title_font.get_text_size(self.title)
            center_x = self.size.width / 2 - text_size.width / 2
            y_off = self.title_spacing[0] + self.border_width
            canvas.text(
                Pos2D(center_x, y_off),
                font=self._title_font,
                text=self.title,
                color=self.title_color,
            )

        self._render_plots(canvas)
        return canvas.to_image()

    def _render_plots(self, canvas):
        """
        Renders the single plots

        :param canvas: The target canvas
        """
        y_off = self.margins[1]
        for cur_row in range(self.row_count):
            x_off = self.margins[0]
            for cur_col in range(self.column_count):
                canvas.push_state()
                if (cur_col, cur_row) in self.plots:
                    self._render_single_plot(canvas, cur_col, cur_row, x_off, y_off)
                canvas.pop_state()
                x_off += self._col_widths[cur_col] + self.grid_spacing.width
            y_off += self._row_heights[cur_row] + self.grid_spacing.height

    def _render_single_plot(self, canvas, cur_col, cur_row, x_off, y_off):
        """
        Renders a single plot

        :param canvas: The tagret canvsa
        :param cur_col: The current column
        :param cur_row: The current row
        :param x_off: The x offset
        :param y_off: The y offset
        """
        plot: Plot = self.plots[(cur_col, cur_row)]
        add_x = 0.0
        add_y = 0.0
        if plot.target_size is not None and plot.size != plot.target_size:
            add_x = (plot.target_size.width - plot.size.width) // 2
            add_y = (plot.target_size.height - plot.size.height) // 2
        canvas.add_offset_shift((x_off + add_x, y_off + add_y))
        plot.paint(canvas)

    def borderless(self, mode: Literal["figure", "plot", "all"] = "all") -> Figure:
        """
        Removes all borders from the figure and (if set so) by default from
        all sub plots.

        :param mode: The removal mode.
            * "figure" - Just remove figure border
            * "plot" - Just remove plot borders
            * "all" - Remove borders from figure and all plots (by default)
        :return:
        """
        if mode in ["figure", "all"]:
            self.border_width = 0
            self.border_margins = [0] * 4
        if mode in ["plot", "all"]:
            self.default_plot_border_width = 0
            self.default_plot_border_margin_size = 0
        return self

    def add_matplot(
        self, col: int = 0, row: int = 0, size_ratio: float = 1.0, **params
    ) -> "MPLayerLock":
        """
        Adds a matplotlib layer and provides access to the matplot functions

        Usage:

        ..  code-block: python

            figure = Figure().borderless("plot")
            with figure.add_matplot(figsize=(4, 4)) as plt:
                plt.title("A grid with random colors")
                data = np.random.default_rng().uniform(0, 1.0, (16, 16, 3))
                plt.imshow(data)

        :param col: The plot's column
        :param row: The plot's row
        :param size_ratio: The size ratio with which the matplot shall be
            integrated. By default the original size
        :param params: The parameters which shall be passed into the figure
            which is going to be created.
        :return: The lock handle
        """
        lock = self.add_plot(col=col, row=row).add_matplot(
            size_ratio=size_ratio, **params
        )
        return lock
