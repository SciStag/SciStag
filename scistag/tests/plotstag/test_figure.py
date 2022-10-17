"""
Tests the Figure class - the container for plots
"""

import pytest

from scistag.plotstag import Figure, Plot
from scistag.plotstag.figure import GridSteppingMode
from .test_image_layer import stag
from . import skip_plotstag


@pytest.mark.skipif(skip_plotstag, reason="PlotStag tests disabled")
def test_grid_stepping():
    """
    Tests the stepping through a grid
    :return:
    """
    figure = Figure(cols=3, rows=3)
    # right -> down
    steps = [figure.get_location(index) for index in range(9)]
    assert steps == [(0, 0), (1, 0), (2, 0),
                     (0, 1), (1, 1), (2, 1),
                     (0, 2), (1, 2), (2, 2)]
    # left -> up
    figure.set_stepping_mode(GridSteppingMode.LEFT_UP)
    steps = [figure.get_location(index) for index in range(9)]
    assert steps == [(2, 2), (1, 2), (0, 2),
                     (2, 1), (1, 1), (0, 1),
                     (2, 0), (1, 0), (0, 0)]
    # down -> right
    figure.set_stepping_mode(GridSteppingMode.DOWN_RIGHT)
    steps = [figure.get_location(index) for index in range(9)]
    assert steps == [(0, 0), (0, 1), (0, 2),
                     (1, 0), (1, 1), (1, 2),
                     (2, 0), (2, 1), (2, 2)]
    figure.set_stepping_mode(GridSteppingMode.UP_LEFT)
    steps = [figure.get_location(index) for index in range(9)]
    # up -> left
    assert steps == [(2, 2), (2, 1), (2, 0),
                     (1, 2), (1, 1), (1, 0),
                     (0, 2), (0, 1), (0, 0)]


@pytest.mark.skipif(skip_plotstag, reason="PlotStag tests disabled")
def test_errors():
    """
    Provoke value errors and fallbacks
    """
    figure = Figure()
    figure.add_plot().add_image(stag, size_ratio=1.0)
    # obsolete mode change
    figure.set_stepping_mode(GridSteppingMode.RIGHT_DOWN)
    # target plot shouldn't work
    assert figure._get_target_plot_size() is None
    # adding a plot twice should return the original
    assert figure.add_plot(0, 0) == figure.plots[(0, 0)]
    # column out of range
    with pytest.raises(IndexError):
        figure.set_plot(column=1, row=0, plot=Plot())
    # row out of range
    with pytest.raises(IndexError):
        figure.set_plot(column=0, row=1, plot=Plot())
    # figure with invalid column count
    with pytest.raises(ValueError):
        Figure(cols=0, rows=1)
    # figure with invalid row count
    with pytest.raises(ValueError):
        Figure(cols=1, rows=0)


@pytest.mark.skipif(skip_plotstag, reason="PlotStag tests disabled")
def test_grid_stepping():
    """
    Tests the grid stepping
    :return:
    """
    assert GridSteppingMode("ld") == GridSteppingMode.LEFT_DOWN
    assert GridSteppingMode("downRight") == GridSteppingMode.DOWN_RIGHT
    