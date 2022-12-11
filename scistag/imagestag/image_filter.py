from __future__ import annotations
import PIL.Image
import numpy as np

from scistag.imagestag.definitions import ImsFramework
from scistag.imagestag.image import Image, ImageSourceTypes
from scistag.imagestag import PixelFormat

IMAGE_FILTER_IMAGE = "image"
"Identifier of the image in the result dict"
IMAGE_FILTER_NAME = "name"
"Identifier of the filter name in the result dict"
IMAGE_FILTER_ORIGINAL_IMAGE = "originalImage"
"Identifier of the original image (if requested)"
IMAGE_FILTER_DATA = "data"
"Identifier of the data in the result dict"
IMAGE_FILTER_MAY_MODIFY = "mayModify"
"If defined the original image may be destroyed by the filter. Can increase the performance."


class ImageFilter:
    """
    Defines the base class for filtering an image.

    Such a filter can be in a range from a simple color to grayscale conversion up to execution of a neural network
    to e.g. detect people in an image.
    """

    def __init__(self):
        """
        Initializer
        """
        self.name = ""
        """
        The filter's name. This can be used to keep track of the intermediate results when using an ImageFilterPipeline.
        """
        self.required_format: str | None = None
        "Can be set to gray, rgb or rgba if the filter requires a special input format"

    def _apply_filter(self, input_data: dict) -> dict:
        """
        Applies the filter to the image. Awaits an "image" object and returns a new "image" and/or the evaluation or
        inference result in "data". Override this method by your needs.
        :param input_data: The input data dictionary containing the image in "image"
        :return: The result data dict, usually containing the filtered image in "image" if not configured
        otherwise.
        """
        return input_data

    def filter(self, input_image: ImageSourceTypes | dict) -> ImageSourceTypes | dict:
        """
        :param input_image: The input image. All common image types are supported. The output type of the filter will
        always match the input type (except in case of a string input of course).
        IMPORTANT: If you need additional output, e.g. objects detected in an image, pass the image in the form
        {"image": imageData} so you will also get a dictionary (containing the results)
        as response.
        :return: The filtered image. The output types matches the input type. In case of a str input an Image will
        be returned. Usually it has the form {"image": resultImage, "data": resultData}. "data" is only present if
        the filter should for example detect something in the image, and it's structure is defined in the specific
        filter in this case.
        """
        original_input = input_image
        if isinstance(input_image, dict):
            if not isinstance(input_image, Image):
                # guarantee the image in the dictionary be an image. do not manipulate the input dict.
                image = input_image[IMAGE_FILTER_IMAGE]
                del input_image[IMAGE_FILTER_IMAGE]
                input_image = input_image.copy()
                input_image[IMAGE_FILTER_IMAGE] = Image(image)
        else:
            input_image = {
                IMAGE_FILTER_IMAGE: Image(input_image, framework=ImsFramework.RAW)
            }
        # convert pixel_format if the filter requires a special pixel_format
        if self.required_format is not None:
            is_gray = input_image[IMAGE_FILTER_IMAGE].pixel_format != PixelFormat.GRAY
            if self.required_format == PixelFormat.GRAY and not is_gray:
                input_image[IMAGE_FILTER_IMAGE] = Image(
                    input_image[IMAGE_FILTER_IMAGE].get_pixels_gray(),
                    framework=ImsFramework.RAW,
                )
            elif (
                self.required_format == PixelFormat.RGB
                or self.required_format == PixelFormat.RGBA
            ) and input_image[IMAGE_FILTER_IMAGE].pixel_format == PixelFormat.GRAY:
                input_image[IMAGE_FILTER_IMAGE] = Image(
                    input_image[IMAGE_FILTER_IMAGE].get_pixels_rgb(),
                    framework=ImsFramework.RAW,
                )
        # execute filter
        result = self._apply_filter(input_image)
        result[IMAGE_FILTER_NAME] = self.name
        # convert to original input pixel_format
        if isinstance(
            original_input, dict
        ):  # if a dictionary was passed in return all details
            return result
        if isinstance(original_input, np.ndarray):  # convert back to numpy array?
            return result[IMAGE_FILTER_IMAGE].get_pixels()
        elif isinstance(original_input, PIL.Image.Image):  # return PIL handle?
            return result[IMAGE_FILTER_IMAGE].to_pil()
        else:  # keep it as imagestag.Image
            return result[IMAGE_FILTER_IMAGE]


__all__ = [
    "ImageFilter",
    "IMAGE_FILTER_IMAGE",
    "IMAGE_FILTER_ORIGINAL_IMAGE",
    "IMAGE_FILTER_DATA",
    "IMAGE_FILTER_MAY_MODIFY",
    "Image",
    "ImsFramework",
]
