from __future__ import annotations
from typing import Tuple, Optional

from scistag.imagestag import Color, InterpolationMethod, Size2DTypes
from scistag.imagestag.image_filter import ImageFilter, IMAGE_FILTER_IMAGE


class ResizeFilter(ImageFilter):
    """
    This filter resizes the image using the provided constraints
    """

    def __init__(
        self,
        size: Optional[tuple[int, int]] = None,
        max_size: Size2DTypes | tuple[int | None, int | None] | None = None,
        keep_aspect: bool = False,
        target_aspect: float | None = None,
        fill_area: bool = False,
        factor: float | None = None,
        interpolation: InterpolationMethod = InterpolationMethod.LANCZOS,
        background_color=Color(0.0, 0.0, 0.0, 1.0),
    ):
        """
        Initializer

        :param size: The target size as tuple (in pixels) (optional)
        :param max_size: The maximum width and/or height to which the image
            shall be scaled while keeping the aspect_ration intact.
            You can pass a maximum width, a maximum height or both.
        :param keep_aspect: Defines if the aspect ratio shall be kept. if set to true the image
           will be zoomed or shrinked equally on both axis so it fits the target size. False by default.
        :param target_aspect: If defined the image will be forced into given aspect ratio by adding "black bars"
            (or the color you defined in "background_color"). Common values are for example 4/3, 16/9 or 21/9.
            Note that this does NOT change the aspect ratio of the real image itself. If you want to change this just
            call this function with the desired "size" parameter.
            It will always preserve the size of the axis to which no black bares are added, so e.g. converting an image
            from 4:3 to 16:9 resulting in black bars on left and right side the original height will be kept. Converting
            an image from 16:9 to 4:3 on the other hand where black bars are added on top and bottom the width will be
            kept. Overrides "size".
        :param fill_area: Defines if the whole area shall be filled with the original image. False by default. Only
            evaluated if keep_aspect is True as well as otherwise a simple definition of "size" would anyway do the job.
        :param factor: Scales the image by given factor. Overwrites size. Can be combined with target_aspect.
            None by default. Overrides "size".
        :param interpolation: The interpolation method.
        :param background_color: The color which shall be used to fill the empty area, e.g. when a certain aspect ratio
            is enforced.
        """
        super().__init__()
        self.size = size
        "The target size in pixels"
        self.max_size = max_size
        "The maximum image size"
        self.keep_aspect = keep_aspect
        "If defined the aspect ratio will be kept intact"
        self.target_aspect = target_aspect
        "If defined the image will be resized to given aspect ratio"
        self.fill_area = fill_area
        "If defined the whole size area will be fill with the image until the shortest side reaches the size"
        self.factor = factor
        "Rescale the image by a fix factor"
        self.interpolation = interpolation
        "The interpolation method to use"
        self.background_color = background_color
        "The color which shall be used to fill the empty area, e.g. when a certain aspect ratio"

    def _apply_filter(self, input_data: dict) -> dict:
        image = input_data[IMAGE_FILTER_IMAGE]
        image = image.resized_ext(
            size=self.size,
            max_size=self.max_size,
            keep_aspect=self.keep_aspect,
            target_aspect=self.target_aspect,
            fill_area=self.fill_area,
            factor=self.factor,
            interpolation=self.interpolation,
            background_color=self.background_color,
        )
        return {IMAGE_FILTER_IMAGE: image}


__all__ = ["ResizeFilter", "Color"]
