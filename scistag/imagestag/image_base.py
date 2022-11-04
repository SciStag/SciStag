"""
Implements the Image's base class :class:`ImageBase` which defines the classes
helper functions and base properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import PIL.Image
import numpy as np

from scistag.imagestag.pixel_format import PixelFormat
from scistag.imagestag.definitions import ImsFramework
from scistag.imagestag import opencv_available, cv

if TYPE_CHECKING:
    from .image import Image


class ImageBase:
    """
    Defines the base class for :class:`Image` and provides object indepedent
    helper methods.
    """

    @classmethod
    def detect_format(cls, pixels: np.ndarray, is_cv2=False):
        """
        Detects the format

        :param pixels: The pixels
        :param is_cv2: Defines if the source was OpenCV
        :return: The pixel format. See PixelFormat
        """
        if len(pixels.shape) == 2:
            return PixelFormat.GRAY
        if is_cv2:
            return PixelFormat.BGR if pixels.shape[2] == 3 else PixelFormat.BGRA
        return PixelFormat.RGB if pixels.shape[2] == 3 else PixelFormat.RGBA

    @classmethod
    def _pixel_data_from_source(cls,
                                source: (str | np.ndarray | bytes |
                                         PIL.Image.Image)) -> np.ndarray:
        """
        Loads an arbitrary source and returns it as pixel data

        :param source: The data source. A filename, a http url, numpy array
            or a PIL image
        :return: The pixel data
        """
        if isinstance(source, np.ndarray):
            return source
        elif isinstance(source, PIL.Image.Image):
            # noinspection PyTypeChecker
            return np.array(source)
        elif isinstance(source, str) or isinstance(source, bytes):
            from .image import Image
            return Image(source, framework=ImsFramework.PIL).get_pixels()
        else:
            raise NotImplemented

    @staticmethod
    def bgr_to_rgb(pixel_data: np.ndarray) -> np.ndarray:
        """
        Converts BGR to RGB or the otherwise round

        :param pixel_data: The input pixel data
        :return: The output pixel data
        """
        if len(pixel_data.shape) == 3 and pixel_data.shape[2] == 3:
            return pixel_data[..., ::-1].copy()
        elif len(pixel_data.shape) == 3 and pixel_data.shape[2] == 4:
            return pixel_data[..., [2, 1, 0, 3]].copy()

    @classmethod
    def normalize_to_rgb(cls, pixels: np.ndarray,
                         input_format: PixelFormat = PixelFormat,
                         keep_gray=False) -> np.ndarray:
        """
        Guarantees that the output will be in the RGB or RGBA format

        :param pixels: The pixel data as :class:`np.ndarray`
        :param input_format: The input format representation, e.g. see
            :class:`.PixelFormat`
        :param keep_gray: Defines if single channel formats shall be kept
            intact. False by default.
        :return: The RGB image as numpy array. If keep_gray was set and the
            input was single channeled the original.
        """
        if len(pixels.shape) == 2:  # grayscale?
            if keep_gray:
                return pixels
            return np.stack((pixels,) * 3, axis=-1)
        if input_format == PixelFormat.BGR or input_format == PixelFormat.BGRA:
            return cls.bgr_to_rgb(pixels)
        else:
            return pixels

    @classmethod
    def normalize_to_bgr(cls, pixels: np.ndarray,
                         input_format: PixelFormat = PixelFormat.RGB,
                         keep_gray=False) -> np.ndarray:
        """
        Guarantees that the output will be in the BGR or BGRA format

        :param pixels: The pixel data
        :param input_format: The input format representation, e.g.
            see :class:`.PixelFormat`
        :param keep_gray: Defines if single channel formats shall be
            kept intact. False by default.
        :return: The BGR image as numpy array. If keep_gray was set and
            the input was single channeled the original.
        """
        if len(pixels.shape) == 2:  # grayscale?
            if keep_gray:
                return pixels
            return np.stack((pixels,) * 3, axis=-1)
        if input_format == PixelFormat.BGR or input_format == PixelFormat.BGRA:
            return pixels
        else:
            return cls.bgr_to_rgb(pixels)

    @classmethod
    def normalize_to_gray(cls, pixels: np.ndarray,
                          input_format: PixelFormat = PixelFormat.RGB) \
            -> np.ndarray:
        """
        Guarantees that the output will be grayscale

        :param pixels: The pixel data :class:`np.ndarray`
        :param input_format: The input format representation,
            e.g. see :class:`.PixelFormat`
        :return: The grayscale image as :class:`np.ndarray`
        """
        if len(pixels.shape) == 2:  # grayscale?
            return pixels
        if input_format in [PixelFormat.BGR, PixelFormat.BGRA]:
            if opencv_available():
                if input_format == PixelFormat.BGR:
                    return cv.cvtColor(pixels, cv.COLOR_BGR2GRAY)
                if input_format == PixelFormat.BGRA:
                    return cv.cvtColor(pixels, cv.COLOR_BGRA2GRAY)
            blue, green, red = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]
        else:
            if opencv_available():
                if input_format == PixelFormat.RGB:
                    return cv.cvtColor(pixels, cv.COLOR_RGB2GRAY)
                if input_format == PixelFormat.RGBA:
                    return cv.cvtColor(pixels, cv.COLOR_RGBA2GRAY)
            red, green, blue = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]
        return (0.2989 * red + 0.5870 * green + 0.1140 * blue).round().astype(
            np.uint8)

    @classmethod
    def from_cv2(cls, pixel_data: np.ndarray) -> "Image":
        """
        Creates an image from a "classic" bgr, bgra or grayscale OpenCV source.

        For more advanced type please use the standard constructor.

        :param pixel_data: The pixel data
        :return: The image instance
        """
        from .image import Image
        return Image(pixel_data,
                     pixel_format=cls.detect_format(pixel_data,
                                                    is_cv2=True))
