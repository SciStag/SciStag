"""
Tests the Plot class - the area within a Figure in which multiple plots can
be stacked on top of each other.
"""
import pytest

from scistag.plotstag import Figure, Plot, MPLock
from .test_image_layer import stag
from . import vl
from . import skip_plotstag

@pytest.mark.skipif(skip_plotstag, reason="PlotStag tests disabled")
def test_plot():
    """
    Tests some advanced basics not covered by the high level class tests
    """
    # test layouting emmpty plot
    plot = Plot()
    plot.update_layout()


@pytest.mark.skipif(skip_plotstag, reason="PlotStag tests disabled")
def test_plotting_methods():
    """
    Tests plotting plots and figures with title
    """
    vl.test("Examples for plotting figures and plots with a title")
    vl.sub_test("A plot with a title")
    figure = Figure()
    figure.add_plot().add_image(stag, size_ratio=1.0).set_title("A stag")
    vl.assert_image("stag_plot", figure.render(),
                    '6aea6c57d9580f0eed58ac84f7cbee3c')
    vl.sub_test("Example for a figure and plot with title")
    figure = Figure(cols=2, rows=2)
    figure.set_title("A group of four stags")
    for index, element in enumerate(figure):
        element.add_image(stag, size_ratio=0.5).set_title(f"Stag #{index + 1}")
    vl.assert_image("stag_plot",
                    figure.render(), '106f8b276e25ec759d412e8a170406f1')
    vl.sub_test("Example for a figure with a title")
    figure = Figure(cols=2, rows=2)
    figure.set_title("A group of four stags")
    for element in figure:
        element.add_image(stag, size_ratio=0.5)
    vl.assert_image("stag_plot",
                    figure.render(), 'a20f515c79365a45461941bcb7e2ee7c')
    pixels = stag.get_pixels_rgb()

    with MPLock() as plt:
        plt.figure(figsize=(5, 4))
        cp = plt.imshow(pixels)
        plt.title("A stag with title")
        plt.tight_layout()
        vl.figure("TestPlot", cp.figure)

    four_figure = Figure(cols=2, rows=2)
    for plot in four_figure:
        with plot.add_matplot(size_ratio=1.0, figsize=(5, 4)) as plt:
            plt.imshow(pixels)
            plt.title("A stag with title")
            plt.tight_layout()
    vl.figure("four_stags", four_figure)

    four_figure = Figure(cols=2, rows=2)
    for plot in four_figure:
        with MPLock() as plt:
            figure = plt.figure(figsize=(4, 3))
            plt.imshow(pixels)
            plt.axis("off")
            plt.title("A custom figure")
            plt.tight_layout()
            plot.add_matplot(figure=figure, size_ratio=1.0)
    vl.figure("four_stags_custom_figure", four_figure)
