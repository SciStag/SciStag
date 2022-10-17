from typing import List

from scistag.imagestag.image_filter import ImageFilter

IMAGE_FILTER_SERIES_STEPS = "steps"
"Intermediate results of a filter"


class ImageFilterSeries(ImageFilter):
    """
    The filter series applies a list of filters to an image in the order they are defined in .filters.
    This way you for example apply multiple filters to a live video stream like so:

    ```
    video_source.set_filter(ImageFilterSeries([GrayscaleFilter(), ColorMapFilter(),ResizeFilter(target_aspect=4.0/3.0)])
    which will first make an image grayscale, then apply a color map filter and afterwards scales it to a
    4:3 ratio.
    ```
    """

    def __init__(self, filters: list[ImageFilter], keep_intermediate: bool = False):
        """
        Initializer
        :param filters: The list of filters
        :param keep_intermediate: Defines if the intermediate results (of the first filters) shall be kept
        """
        super(ImageFilterSeries, self).__init__()
        self.keep_intermediate = keep_intermediate
        "If set all intermediate results will be returned in steps"
        self.filters: list[ImageFilter] = filters
        "The lister of filters to apply"

    def _apply_filter(self, input_data: dict) -> dict:
        cur_data = input_data
        steps = []
        for cur_filter in self.filters:
            cur_filter: ImageFilter
            cur_data = cur_filter.filter(cur_data)
            if self.keep_intermediate:
                steps += cur_data
        return cur_data
