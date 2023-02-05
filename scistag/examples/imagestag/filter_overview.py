"""
This demo gives a coarse overview of the most common filters ImageStag provides
"""
from __future__ import annotations

import numpy as np

from scistag.imagestag import Image, get_opencv
from scistag.mediastag import CameraCv2
from scistag.vislog import LogBuilder, cell, stream
from scistag.vislog.widgets import LSelect


class FilterDemo(LogBuilder):
    def __init__(self, **kwargs):
        """
        Initializer, sets up the camera and video streaming
        """
        super().__init__(**kwargs)
        self.video_source = CameraCv2(0)
        self.video_source.start()
        self.video_ts = 0.0

    @cell
    def header(self):
        """
        Just some header decoration
        """
        self.title("ImageStag Basic Filter Overview")

    @cell(output="curFilter")
    def filter_selection(self):
        """
        Provides a filter selection box
        """
        filters = [
            ("Canny", "canny"),
            ("Sobel", "sobel"),
            ("Gray", "gray"),
            ("Heat", "heat"),
            ("HSV", "hsv"),
        ]
        self.table(
            [
                [
                    "**Select filter **",
                    lambda: LSelect(self, elements=filters, target="curFilter"),
                ]
            ],
            mimetype="md",
            seamless=True,
        )
        self.br()

    @stream(continuous=True, output="filteredImage")
    def image_receiver(self):
        """
        Receives the image from the webcam and stores it in currentImage
        """
        new_timestamp, new_image = self.video_source.get_image(self.video_ts)
        if new_image is not None:
            self.video_ts = new_timestamp
            self["currentImage"] = new_image

    @stream(requires=["currentImage", "curFilter"], output=["filteredImage"])
    def filter(self):
        """
        Applies the filter to the image
        """
        normalized: Image = self["currentImage"].resized_ext(max_size=(1280, 1280))
        cur_filter = self["curFilter"]
        if cur_filter == "gray":
            normalized = Image(normalized.get_pixels_gray())
        elif cur_filter == "canny":
            normalized = Filters.apply_canny(normalized)
        elif cur_filter == "sobel":
            normalized = Filters.apply_sobel(normalized)
        elif cur_filter == "heat":
            normalized = Image.from_array(normalized.get_pixels_gray(), cmap="magma")
        elif cur_filter == "hsv":
            normalized = Filters.apply_hsv(normalized)
        self["filteredImage"] = normalized

    @cell(requires="filteredImage", interval_s=0.0)
    def show_image(self):
        """
        Visualizes the image
        """
        self.image(self["filteredImage"], filetype=("jpg", 80), scaling=1.0)


class Filters:
    """
    A collection of basic filters samples.

    TODO: To be moved to re-usable ImageStag filters
    """

    @staticmethod
    def apply_canny(image: Image) -> Image:
        """
        Applies the Canny edge detection filter

        :param image: The original
        :return: Visualization of the detected edges
        """
        cv = get_opencv()
        return cv.Canny(image.get_pixels_bgr(), 100, 200, 12)

    @staticmethod
    def apply_hsv(image: Image) -> Image:
        """
        Splits the image into hue, saturation and value and visualizes it as
        grid of 2x2 next to the grayscale original

        :param image: The original image
        :return: The grid
        """
        image = image.resized_ext(factor=0.5)
        gray = image.get_pixels_gray()
        image = image.convert("HSV")
        pixels: np.ndarray = image.get_pixels()
        return Image(
            np.vstack(
                [
                    np.hstack([gray, pixels[:, :, 0]]),
                    np.hstack([pixels[:, :, 1], pixels[:, :, 2]]),
                ]
            )
        )

    @staticmethod
    def apply_sobel(image: Image) -> Image:
        """
        Applies the sobel filter to the image

        :param image: The original image
        :return: The image with highlighted edges
        """
        cv = get_opencv()
        ddepth = cv.CV_16S
        scale = 1
        delta = 0
        src = cv.GaussianBlur(image.get_pixels_rgb(), (3, 3), 0)
        gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
        grad_x = cv.Sobel(
            gray,
            ddepth,
            1,
            0,
            ksize=3,
            scale=scale,
            delta=delta,
            borderType=cv.BORDER_DEFAULT,
        )
        grad_y = cv.Sobel(
            gray,
            ddepth,
            0,
            1,
            ksize=3,
            scale=scale,
            delta=delta,
            borderType=cv.BORDER_DEFAULT,
        )
        abs_grad_x = cv.convertScaleAbs(grad_x)
        abs_grad_y = cv.convertScaleAbs(grad_y)
        image = Image(cv.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0))
        return image


FilterDemo.run(title="ImageStag basic filters", as_service=True)
