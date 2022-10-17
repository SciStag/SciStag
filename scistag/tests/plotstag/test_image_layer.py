"""
Tess the image layer o a plot
"""
import pytest

from scistag.emojistag import get_emoji
from scistag.plotstag import Figure, Plot
from scistag.common import get_test_image, TestDataNames
from . import vl
from . import skip_plotstag

stag = get_test_image(TestDataNames.STAG)


@pytest.mark.skipif(skip_plotstag, reason="PlotStag tests disabled")
def test_image_layer():
    """
    Tests the basic painting functions of an image layer"
    """
    vl.test("Examples for simple image plotting")
    vl.sub_test("Single image plot")
    figure = Figure()
    figure.add_plot().add_image(stag, size_ratio=1.0)
    vl.assert_image("stag_plot",
                    source=figure.render(),
                    hash_val="feea4ff3bf44549193f7987ec0e24640")
    vl.sub_test("2x2 Grid with relative image size")
    grid = Figure(cols=2, rows=2)
    for plot in grid:
        plot.add_image(stag, size_ratio=0.5)
    vl.assert_image("stag_plot_grid",
                    grid.render(),
                    'cef5728cd115c95907ab1d521073b8be')


@pytest.mark.skipif(skip_plotstag, reason="PlotStag tests disabled")
def test_partial():
    """
    Tests partially filled grids
    """
    vl.test("Advanced image plotting")
    vl.sub_test("2x2 Grid with one element missing")
    grid = Figure(cols=2, rows=2)
    for plot, index in zip(grid, range(3)):
        plot.add_image(stag, size_ratio=0.5)
    image = grid.render()
    vl.assert_image("stag_plot_grid",
                    image,
                    "35e06aedecd8c2c0943bca188dbe2289")
    vl.sub_test("Skipping the third element")
    grid = Figure(cols=2, rows=2)
    for index in range(3):
        if index == 2:
            index += 1
        pos = grid.get_location(index)
        grid.set_plot(Plot().add_image(stag, size_ratio=0.5), column=pos[0],
                      row=pos[1])
    image = grid.render()
    vl.assert_image("stag_plot_grid",
                    image, 'b85f612273f10a9faec2f76b6cc55b10')


@pytest.mark.skipif(skip_plotstag, reason="PlotStag tests disabled")
def test_auto_scale():
    """
    Tests tha automatic scaling of plots
    """
    vl.test("Examples for auto scaling plots")
    vl.sub_test("2x2 grid with auto-scaling plot and without figure border")
    grid = Figure(cols=2, rows=2)
    for plot in grid:
        plot.add_image(stag)
    grid.border_width = 0.0  # test missing figure border
    image = grid.render()
    vl.assert_image("stag_plot_grid", image,
                    "9545183f53384536df2016ddd1bbb0d2")
    vl.sub_test("2x2 grid with precisely defined size")
    grid = Figure(cols=2, rows=2, size=(800, 700))
    for index, plot in enumerate(grid):
        plot.border_width = 0.0  # test missing grid border
        plot.add_image(stag)
        assert index == plot.index
        pos = grid.get_location(index)
        assert plot.column == pos[0] and plot.row == pos[1]
    image = grid.render()
    vl.assert_image("stag_plot_grid", image, '9a0dd8830d42aa9fdc6b0a39d8f8f257')
    assert image.width == 800 and image.height == 700
    vl.sub_test("A 2x2 grid with plot-wise default size")
    grid = Figure(cols=2, rows=2, plot_size=(400, 400))
    for plot in grid:
        plot.add_image(stag)
    image = grid.render()
    vl.assert_image("stag_plot_grid",
                    image, 'd18186d4c7e9c0ce8e143824317fb5d4')
    vl.sub_test(
        "Example for automatic figure creation when a grid's render method "
        "is called directly")
    image = Plot().add_image(stag).get_figure().render()
    vl.assert_image("stag_plot_grid", image,
                    'eb57b784224bf3df4cef4578b30e6fc5')
    vl.sub_test("A 2x2 grid created using a direct plot call")
    image = Plot().add_image(stag, size_ratio=0.5).render()
    vl.assert_image("stag_plot_grid", image, '58dbc1ffe4d490d18473e115f913ead4')


@pytest.mark.skipif(skip_plotstag, reason="PlotStag tests disabled")
def test_transparent_image():
    """
    Tests plotting an alpha-transparent image
    """
    vl.test("Plotting transparent images")
    stag_emoji = get_emoji(":deer:", size=505)
    image = Figure().add_plot().add_image(stag_emoji, size_ratio=1.0).render()
    vl.assert_image("stag_plot_alpha_transparent",
                    image, 'db94e195188cc3efafd84606aa7fe39a')
