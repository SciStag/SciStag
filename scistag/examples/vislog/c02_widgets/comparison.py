"""
This demo shows how you can use the LComparison widget to compare two images
"""
from scistag.imagestag import Image
from scistag.vislog import VisualLog, LogBuilder, cell
from scistag.vislog.widgets import LComparison


class ComparatorExample(LogBuilder):
    @cell
    def show_comparison(self):
        self.title("Image comparison demo")
        self.br().add(
            "Drag the slider to the left or to the right to see the impact "
            "of the filter applied."
        ).br()
        with self.align.block_center:
            # create the globe emoji and a grayscale representation of it
            image_a = self.emoji("*globe*", return_image=True, size=512)
            image_b = Image.from_array(
                image_a.get_pixels_gray(), cmap="magma", min_val=0, max_val=255
            )
            LComparison(self, [image_a, image_b], style=LComparison.Style.HOR_SPLIT)


if VisualLog.is_main():
    VisualLog().run_server(ComparatorExample, auto_reload=True)
