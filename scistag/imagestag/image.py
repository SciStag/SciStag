"""
Implements the class :class:`.Image` which is SciStag's main class for loading,
storing and keeping image data in memory.
"""
from __future__ import annotations
import hashlib
import io
import os
from typing import Union, TYPE_CHECKING, Any

import PIL.Image
import numpy as np

from .color import Color, Colors
from .bounding import Bounding2DTypes, Bounding2D
from .interpolation import InterpolationMethod
from .pixel_format import PixelFormat
from .size2d import Size2D, Size2DTypes
from .definitions import ImsFramework, opencv_available, cv
from .image_base import ImageBase
from ..filestag import FileStag

if TYPE_CHECKING:
    from scistag.imagestag.canvas import Canvas

SUPPORTED_IMAGE_FILETYPES = ["png", "bmp", "jpg", "jpeg", "gif"]
"List of image file types which can be read and written"

SUPPORTED_IMAGE_FILETYPE_SET = set(SUPPORTED_IMAGE_FILETYPES)
"Set of image file types which can be read and written"

Image = type

ImageSourceTypes = Union[str, np.ndarray, bytes, PIL.Image.Image, Image]
"The valid source type for loading an image"


class Image(ImageBase):
    """
    SciStag's default class for storing image data in all common pixel formats.


    The data is internally either stored using the PILLOW image library's Image
    class or as a classical numpy array, depending on how it was initialized.
    If not specified otherwise it will always the PILLOW representation
    as this is very well suited to visualize the data or modify it using the
    Canvas class.

    If you want to access the data directly you can at all times call the to_pil
    or get_pixels function.

    Usage example:

    ..  literalinclude:: /../../scistag/examples/imagestag/image.py
        :language: python
    """

    def __init__(self, source: ImageSourceTypes | None = None,
                 framework: ImsFramework = None,
                 pixel_format: PixelFormat | None = None,
                 size: Size2DTypes | None = None,
                 bg_color: Color | None = None,
                 **params):
        """
        :param source: The image source. Either a file name, a http URL,
            numpy array or one of the supported low level types. Note that
            the pixel source you refer, e.g. a PIl image or a numpy array
            might be referenced directly and modified by this object.

            Files from the web are cached by default if not disabled
            otherwise via cache=False using WebStag's default caching duration
            and size.
        :param framework: The framework to be used if the file is loaded from
            disk
        :param pixel_format: The pixel format - if the data was passed
            as np.array. RGB by default.
        :param size: The size of the new image (if no source ia passed)
        :param bg_color: The background color of the new image
        :param params: Source protocol dependent, additional loading parameters

        Raises a ValueError if the image could not be loaded
        """
        if size is not None:
            size = Size2D(size) if not isinstance(size, Size2D) else size
            if bg_color is None:
                bg_color = Colors.BLACK
            if source is not None:
                raise ValueError("Can not pass a source and an image size of "
                                 "a new image")
            if pixel_format is None:
                pixel_format = PixelFormat.RGB
            from .canvas import Canvas
            canvas = Canvas(size=size, default_color=bg_color,
                            image_format=pixel_format)
            source = canvas.target_image
        if pixel_format is None:
            pixel_format = PixelFormat.RGB
        self.width = 1
        "The image's width in pixels"
        self.height = 1
        "The image's height in pixels"
        self.framework = framework if framework is not None else \
            ImsFramework.PIL
        "The framework being used. ImsFramework.PIL by default."
        self._pil_handle: PIL.Image.Image | None = None
        "The PILLOW handle (if available)"
        self._pixel_data: np.ndarray | None = None
        "The pixel data (if available) as numpy array"
        self.pixel_format: PixelFormat = pixel_format
        "The base format (rgb, rbga, bgr etc.)"
        # ------- preparation of source data -------
        source, self.pixel_format = \
            self._prepare_data_source(framework, source,
                                      self.pixel_format, **params)
        # ------------------------------------------
        if framework is None:
            framework = ImsFramework.PIL
        if framework == ImsFramework.PIL:
            self._init_as_pil(source)
        elif framework == ImsFramework.RAW:
            self._pixel_data = self._pixel_data_from_source(source)
            self.height, self.width = self._pixel_data.shape[0:2]
            self.pixel_format = self.detect_format(self._pixel_data)
        elif framework == ImsFramework.CV:
            self._init_as_cv2(source)
        else:
            raise NotImplementedError
        self.initialized = True
        self._read_only = {"width", "height", "pixel_format", "framework"}

    def __setattr__(self, key, value):
        if "_read_only" in self.__dict__:
            if key in self.__dict__:
                raise ValueError(
                    f"{key} can not be modified after initialization")
        self.__dict__[key] = value

    def _repr_png_(self) -> bytes:
        """
        PNG representation for Jupyter

        :return: The PNG data
        """
        return self.to_png()

    @classmethod
    def _prepare_data_source(cls,
                             framework: ImsFramework,
                             source: ImageSourceTypes,
                             pixel_format: PixelFormat,
                             **params):
        """
        Prepares and if necessary converts the data source to a supported format

        :param framework: The framework being used
        :param source: The source, a byte steam, a filename or a http URL
        :param params: Source protocol dependent, additional loading parameters
        :return: The prepared source data
        """
        if isinstance(source, cls):
            source = source.to_pil()
        if isinstance(source,
                      np.ndarray) and pixel_format == PixelFormat.BGR and \
                framework != ImsFramework.CV:
            source = cls.normalize_to_rgb(source, keep_gray=True,
                                          input_format=pixel_format)
            pixel_format = cls.detect_format(source)
        # fetch from web if desired
        if isinstance(source, str):
            if source.startswith("http://") or source.startswith("http:s//"):
                params['cache'] = params.get("cache", True)
            source = FileStag.load_file(source, **params)
            if source is None:
                raise ValueError("Image data could not be received")
        return source, pixel_format

    def _init_as_cv2(self, source: np.ndarray):
        """
        Initializes the image from a numpy array and assuming OpenCV's BGR /
        BGRA color channel order

        :param source: The data source
        """
        if isinstance(source, np.ndarray):
            self._pixel_data = \
                self.normalize_to_bgr(source,
                                      input_format=self.pixel_format,
                                      keep_gray=True)
            self.pixel_format = self.detect_format(self._pixel_data,
                                                   is_cv2=True)
        else:
            self._pixel_data = Image(source).get_pixels(PixelFormat.BGR)
            self.pixel_format = self.detect_format(self._pixel_data,
                                                   is_cv2=True)
        self.height, self.width = self._pixel_data.shape[0:2]

    def _init_as_pil(self, source):
        """
        Initializes the image as PIL image

        :param source: The data source
        """
        if isinstance(source, str):
            self._pil_handle = PIL.Image.open(source)
        elif isinstance(source, bytes):
            data = io.BytesIO(source)
            self._pil_handle = PIL.Image.open(data)
        elif isinstance(source, np.ndarray):
            self._pil_handle = PIL.Image.fromarray(source)
        elif isinstance(source, PIL.Image.Image):
            self._pil_handle = source
        else:
            raise NotImplementedError
        if self._pil_handle.mode == "P":
            if 'transparency' in self._pil_handle.info:
                self._pil_handle = self._pil_handle.convert("RGBA")
            else:
                self._pil_handle = self._pil_handle.convert("RGB")
        self.width = self._pil_handle.width
        self.height = self._pil_handle.height
        pf = self._pil_handle.mode.lower()
        self.pixel_format = PixelFormat.from_pil(pf)

    def is_bgr(self) -> bool:
        """
        Returns if the current format is bgr or bgra

        :return: True if the image currently in bgr or bgra format
        """
        return (self.pixel_format == PixelFormat.BGR or self.pixel_format ==
                PixelFormat.BGRA)

    def get_size(self) -> tuple[int, int]:
        """
        Returns the image's size in pixels

        :return: The size as tuple (width, height)
        """
        return (self.width, self.height)

    def get_size_as_size(self) -> Size2D:
        """
        Returns the image's size

        :return: The size
        """
        return Size2D(self.width, self.height)

    def cropped(self, box: Bounding2DTypes) -> Image:
        """
        Crops a region of the image and returns it

        :param box: The box in the form x, y, x2, y2
        :return: The image of the defined subregion
        """
        box = Bounding2D(box)
        box = box.to_int_coord_tuple()
        if box[2] < box[0] or box[3] < box[1]:
            raise ValueError(
                "X2 or Y2 are not allowed to be smaller than X or Y")
        if box[0] < 0 or box[1] < 0 or box[2] >= self.width or box[
            3] >= self.height:
            raise ValueError("Box region out of image bounds")
        if self._pil_handle:
            return Image(self._pil_handle.crop(box=box))
        else:
            cropped = self._pixel_data[box[1]:box[3], box[0]:box[2],
                      :] if len(self._pixel_data.shape) == 3 \
                else self._pixel_data[box[1]:box[3] + 1, box[0]:box[2] + 1]
            return Image(cropped, framework=self.framework,
                         pixel_format=self.pixel_format)

    def resize(self, size: Size2DTypes):
        """
        Resizes the image to given resolution (modifying this image directly)

        :param size: The new size
        :param _no_opencv: Defines if OpenCV usage is forbidden
        """
        size = Size2D(size).to_int_tuple()
        if size[0] == self.width and size[1] == self.height:
            return
        if self.framework == ImsFramework.PIL:
            self.__dict__["_pil_handle"] = \
                self._pil_handle.resize(size,
                                        PIL.Image.Resampling.LANCZOS)
        else:
            if opencv_available():
                self.__dict__["_pixel_data"] = \
                    cv.resize(self._pixel_data, dsize=size,
                              interpolation=cv.INTER_LANCZOS4)
            else:
                image = Image(self._pixel_data, framework=ImsFramework.PIL,
                              pixel_format=self.pixel_format)
                image.resize(size)
                self.__dict__["_pixel_data"] = image.get_pixels(
                    desired_format=self.pixel_format)
        self.__dict__["width"], self.__dict__["height"] = size

    def resized(self, size: Size2DTypes) -> "Image":
        """
        Returns an image resized to given resolution

        :param size: The new size
        """
        size = Size2D(size).to_int_tuple()
        if self.width == size[0] and self.height == size[1]:
            return self
        if self.framework == ImsFramework.PIL:
            return Image(
                self._pil_handle.resize(size, PIL.Image.Resampling.LANCZOS),
                framework=ImsFramework.PIL)
        else:
            return Image(
                self.to_pil().resize(size, PIL.Image.Resampling.LANCZOS))

    def resized_ext(self, size: Size2DTypes | None = None,
                    max_size: Size2DTypes | tuple[
                        int | None, int | None] | None = None,
                    keep_aspect: bool = False,
                    target_aspect: float | None = None,
                    fill_area: bool = False,
                    factor: float | tuple[float, float] | None = None,
                    interpolation: InterpolationMethod =
                    InterpolationMethod.LANCZOS,
                    background_color=Color(0.0, 0.0, 0.0, 1.0)) -> "Image":
        """
        Returns a resized variant of the image with many configuration
        possibilities.

        :param size: The target size as tuple (in pixels) (optional)
        :param max_size: The maximum width and/or height to which the image
            shall be scaled while keeping the aspect_ration intact.
            You can pass a maximum width, a maximum height or both.
        :param keep_aspect: Defines if the aspect ratio shall be kept.
            if set to true the image will be zoomed or shrunk equally on both
            axis so it fits the target size. False by default.
        :param target_aspect: If defined the image will be forced into given
            aspect ratio by adding "black bars" (or the color you defined in
            "background_color"). Common values are for example 4/3, 16/9 or
            21/9.

            Note that this does NOT change the aspect ratio of the real image
            itself. If you want to change this just call this function with the
            desired "size" parameter.

            It will always preserve the size of the axis to which no black bares
            are added, so e.g. converting an image from 4:3 to 16:9 resulting in
            black bars on left and right side the original height will be kept.

            Converting an image from 16:9 to 4:3 on the other hand where black
            bars are added on top and bottom the width will be kept.
            Overrides "size".
        :param fill_area: Defines if the whole area shall be filled with the
            original image.

            False by default. Only evaluated if keep_aspect is
            True as well as otherwise a simple definition of "size" would anyway
            do the job.
        :param factor: Scales the image by given factor. Overwrites size.

            Can be combined with target_aspect.  None by default.
            Overrides "size".
        :param interpolation: The interpolation method.
        :param background_color: The color which shall be used to fill the empty
            area, e.g. when a certain aspect ratio is enforced.
        """
        size = Size2D(size).to_int_tuple() if size is not None else None
        if max_size is not None:
            size = self. \
                compute_rescaled_size_from_max_size(max_size,
                                                    self.get_size_as_size())
        handle = self.to_pil()
        resample_method = interpolation.to_pil()
        int_color = background_color.to_int_rgba()
        bordered_image_size = None
        # target image size (including black borders)
        if keep_aspect and size is not None:
            if factor is not None and not isinstance(factor, float):
                raise ValueError("Can not combine a tuple factor "
                                 "with keep_aspect")
            if fill_area:
                factor = max([size[0] / self.width, size[1] / self.height])
                virtual_size = int(round(factor * self.width)), int(
                    round(factor * self.height))
                ratio = size[0] / virtual_size[0], size[1] / virtual_size[1]
                used_pixels = int(round(self.width * ratio[0])), int(
                    round(self.height * ratio[1]))
                offset = self.width // 2 - used_pixels[
                    0] // 2, self.height // 2 - used_pixels[1] // 2
                return Image(handle.resize(size, resample=resample_method,
                                           box=(offset[0], offset[1],
                                                offset[0] + used_pixels[0] - 1,
                                                offset[1] + used_pixels[
                                                    1] - 1)))
            else:
                bordered_image_size = size
                factor = min([size[0] / self.width, size[1] / self.height])
        if fill_area:
            raise ValueError(
                'fill_area==True without keep_aspect==True has no effect. '
                'If you anyway just want to ' +
                'fill the whole area with the image just provide "size" and '
                'set "fill_area" to False')
        if target_aspect is not None:
            factor = (1.0, 1.0) if factor is None else factor
            if isinstance(factor, float):
                factor = (factor, factor)
            if size is not None:
                raise ValueError(
                    '"target_aspect" can not be combined with "size" but just '
                    'with factor. ' +
                    'Use "size" + "keep_aspect" instead if you know the desired '
                    'target size already.')
            # if the image shall also be resized
            size = int(round(self.width * factor[0])), int(
                round(self.height * factor[1]))
        if factor is not None:
            if isinstance(factor, float):
                factor = (factor, factor)
            size = int(round(self.width * factor[0])), int(
                round(self.height * factor[1]))
        assert size is not None and size[0] > 0 and size[1] > 0
        if size != (self.width, self.height):
            handle = handle.resize(size, resample=resample_method)
        if target_aspect is not None:
            rs = 1.0 / target_aspect
            cur_aspect = self.width / self.height
            if cur_aspect < target_aspect:
                # if cur_aspect is smaller we need to add black bars
                # to the sides
                bordered_image_size = (
                    int(round(self.height * target_aspect * factor[0])),
                    int(round(self.height * factor[1])))
            else:  # otherwise to top and bottom
                bordered_image_size = (int(round(self.width * factor[0])),
                                       int(round(self.width * rs ** factor[1])))
        if bordered_image_size is not None:
            new_image = PIL.Image.new(handle.mode, bordered_image_size,
                                      int_color)
            position = (new_image.width // 2 - handle.width // 2,
                        new_image.height // 2 - handle.height // 2)
            new_image.paste(handle, position)
            return Image(new_image)
        return Image(handle)

    def compute_rescaled_size_from_max_size(self,
                                            max_size,
                                            org_size: Size2D) -> \
            tuple[int, int]:
        """
        Computes the new size of an image after rescaling with a given
        maximum width and/or height and a given original size.

        :param max_size: The maximum size or a tuple containing the maximum
            width, height or both
        :param org_size: The original size
        :return: The effective size in pixels
        """
        if isinstance(max_size, tuple) and len(max_size) == 2:
            max_width = \
                int(round(max_size[0])) if max_size[0] is not None else None
            max_height = \
                int(round(max_size[1])) if max_size[1] is not None else None
        else:
            max_size = Size2D(max_size)
            max_width, max_height = max_size.to_int_tuple()
        if max_width is not None:
            if max_height is not None:
                scaling = min([max_width / self.width,
                               max_height / self.height])
            else:
                scaling = max_width / self.width
        elif max_height is not None:
            scaling = max_height / self.height
        else:
            raise ValueError(
                "Neither a valid maximum width nor height passed")
        return (int(round(org_size.width * scaling)),
                int(round(org_size.height * scaling)))

    def convert(self, target_format: PixelFormat | str,
                bg_fill: Union["Color", None] = None) -> Image:
        """
        Converts the image's format

        :param target_format: The target format
        :param bg_fill: For alpha-transparent images only: The color of the
            background of the new non-transparent image.
        :return: Self
        """
        target_format = PixelFormat(target_format)
        original = self._pil_handle
        if original is None:  # ensure a handle is available
            original = self.to_pil()
        pil_format = target_format.to_pil()
        if pil_format is None:
            raise NotImplementedError("The conversion to this format is "
                                      "currently not supported")
        if target_format == PixelFormat.RGB and original.mode == "RGBA":
            new_image = Image(pixel_format=PixelFormat.RGB,
                              size=self.get_size(),
                              bg_color=bg_fill)
            pil_handle = new_image.to_pil()
            pil_handle.paste(original, (0, 0), original)
            self.__dict__['_pil_handle'] = pil_handle
        else:
            self.__dict__['_pil_handle'] = original.convert(pil_format)
        self.__dict__['framework'] = ImsFramework.PIL
        self.__dict__['pixel_format'] = target_format
        self.__dict__['_pixel_data'] = None
        return self

    def convert_to_raw(self) -> Image:
        """
        Converts the image to use the RAW framework which is faster if you
        excessively access the pixel data frequently.
        """
        if self.framework == ImsFramework.RAW:
            return self
        self.__dict__['_pixel_data'] = self.get_pixels()
        self.__dict__['_pil_handle'] = None
        self.__dict__['framework'] = ImsFramework.RAW
        return self

    def convert_to_pil(self) -> Image:
        """
        Converts the image to use the RAW framework which is faster if you
        excessively access the pixel data frequently.
        """
        if self.framework == ImsFramework.PIL:
            return self
        new_format = self.pixel_format.to_pil()
        if new_format is None:
            raise NotImplementedError("This color format is not supported")
        pixels = self.get_pixels()
        self.__dict__['_pil_handle'] = PIL.Image.fromarray(pixels,
                                                           mode=new_format)
        self.__dict__['_pixel_data'] = None
        self.__dict__['framework'] = ImsFramework.PIL
        return self

    def copy(self) -> Image:
        """
        Creates a copy of this image.

        By default a PILLOW based image will be created

        :return: A copy of this image
        """
        return Image(self.to_pil().copy())

    def get_handle(self) -> np.ndarray | PIL.Image.Image:
        """
        Returns the low level data handle, for example a numpy array or
        a PIL handle.

        Do not use this to modify the data and be aware of the the type could
        change dynamically. Use method:`~get_pixels` or :method:`~to_pil` if
        you need a guaranteed type.

        :return: The handle
        """
        return self._pil_handle if self.framework == ImsFramework.PIL else \
            self._pixel_data

    def get_pixels(self,
                   desired_format: PixelFormat | None = None) -> np.ndarray:
        """
        Returns the image's pixel data as :class:`np.ndarray`.

        Note that manipulating the data will has no effect to the image if the
        internal representation is not a numpy array.

        :param desired_format: The desired output pixel format, e.g. see
            :class:`PixelFormat`. By default the own format
        :return: The numpy array containing the pixels
        """
        if desired_format is None:
            desired_format = self.pixel_format
        if self.framework != ImsFramework.PIL:  # not PIL
            pixel_data = self._pixel_data
        else:
            image: PIL.Image.Image = self._pil_handle
            # noinspection PyTypeChecker
            pixel_data = np.array(image)
        if self.pixel_format == desired_format:
            return pixel_data
        to_rgb = (desired_format == PixelFormat.RGB or
                  desired_format == PixelFormat.RGBA)
        if self.pixel_format not in {PixelFormat.RGB,
                                     PixelFormat.RGBA} and to_rgb:
            return self.normalize_to_rgb(pixel_data,
                                         input_format=self.pixel_format)
        elif desired_format == PixelFormat.GRAY:
            return self.normalize_to_gray(pixel_data,
                                          input_format=self.pixel_format)
        elif (desired_format == PixelFormat.BGR or
              desired_format == PixelFormat.BGRA):
            pixel_data = self.normalize_to_bgr(pixel_data,
                                               input_format=self.pixel_format)
            return pixel_data
        raise NotImplementedError("The request conversion is not supported yet")

    def split(self) -> list[np.ndarray]:
        """
        Returns the single bands as single channels.

        In difference to :meth:`get_pixels` the data is reshaped to
        channel x height x width so each channel can be handled separately.

        Single band channels (such as gray) also guarantee a three dimensional
        shape. (1 x Height x Width)

        :return: The single channels.
        """
        data = self.get_pixels()
        if len(data.shape) == 2:
            return [data]
        else:
            result = np.dsplit(data, data.shape[-1])
            result = [element.reshape((self.height, self.width)) for element in
                      result]
            return result

    def get_band_names(self) -> list[str]:
        """
        Returns the names of the single color bands

        :return: The name of the bands
        """
        return self.pixel_format.get_band_names()

    def get_pixels_rgb(self) -> np.ndarray:
        """
        Returns the pixels and ensures they are either rgb or rgba
        """
        return self.get_pixels(desired_format=PixelFormat.RGB)

    def get_pixels_bgr(self) -> np.ndarray:
        """
        Returns the pixels and ensures they are either bgr or bgra
        """
        return self.get_pixels(desired_format=PixelFormat.BGR)

    @property
    def __array_interface__(self) -> dict:
        """
        Conversion to numpy representation

        :return: A dictionary containing shape,typestr and data to be loaded
            into a numpy array
        """
        data = {}
        bands = self.pixel_format.bands
        data_type = self.pixel_format.data_type
        shape = (self.height, self.width) if bands == 1 else \
            (self.height, self.width, bands)
        data_type_str = "|i1" if data_type == int or data_type == np.uint else \
            "|f4" if data_type == float else "|u1"
        data["shape"] = shape
        data["typestr"] = data_type_str
        data["version"] = 3
        data["data"] = self.to_pil().tobytes()
        return data

    def to_cv2(self) -> np.ndarray:
        """
        Converts the pixel data from the current format to it's counter
        type in OpenCV

        :return: The OpenCV numpy data
        """
        return self.get_pixels_bgr() if self.pixel_format != PixelFormat.GRAY \
            else self.get_pixels(desired_format=PixelFormat.GRAY)

    def get_pixels_gray(self) -> np.ndarray:
        """
        Returns the pixels and ensures they are gray scale
        """
        return self.get_pixels(desired_format=PixelFormat.GRAY)

    def to_pil(self) -> PIL.Image.Image:
        """
        Converts the image to a PIL image object

        :return: The PIL image
        """
        if self._pil_handle is not None:
            return self._pil_handle
        else:
            pixel_data = self.get_pixels()  # guarantee RGB
            return PIL.Image.fromarray(pixel_data)

    def to_canvas(self) -> "Canvas":
        """
        Converts the image to a canvas (if possible)

        :return: The canvas handle
        """
        if self._pil_handle is None:
            raise NotImplementedError("Canvas conversion is only supported "
                                      "for PIL based images")
        from scistag.imagestag.canvas import Canvas
        return Canvas(target_image=self)

    def encode(self, filetype: str = "png", quality: int = 90,
               background_color: Color | None = None) -> bytes | None:
        """
        Compresses the image and returns the compressed file's data as bytes
        object.

        :param filetype: The output file type. Valid types are
            "png", "jpg"/"jpeg", "bmp" and "gif"
        :param quality: The image quality between (0 = worst quality) and
            (95 = best quality). >95 = minimal loss
        :param background_color: The background color to store an RGBA image as
            RGB image.
        :return: The bytes object if no error occurred, otherwise None
        """
        image = self
        filetype = filetype.lstrip(".").lower()
        if filetype == "jpg":
            filetype = "jpeg"
        if self.is_transparent() and (filetype != "png" or background_color is
                                      not None):
            from scistag.imagestag import Canvas
            color = Colors.WHITE if background_color is None else \
                background_color
            white_canvas = Canvas(size=self.get_size(),
                                  default_color=color)
            white_canvas.draw_image(self, (0, 0))
            image = white_canvas.to_image()
        assert filetype in SUPPORTED_IMAGE_FILETYPE_SET
        parameters = {}
        if filetype.lower() in {"jpg", "jpeg"}:
            assert 0 <= quality <= 100
            parameters["quality"] = quality
        output_stream = io.BytesIO()
        image.to_pil().save(output_stream, format=filetype, **parameters)
        data = output_stream.getvalue()
        return data if len(data) > 0 else None

    def to_png(self, quality: int = 90, **params) -> bytes | None:
        """
        Encodes the image as png.

        :param quality: The compression grade (no impact on quality).
        :param params: Advanced encoding params. See :meth:`encode`
        :return: The image as bytes object
        """
        return self.encode("png", quality, **params)

    def to_jpeg(self, quality: int = 90, **params) -> bytes | None:
        """
        Encodes the image as jpeg.

        :param quality: The compression grade.
        :param params: Advanced encoding params. See :meth:`encode`
        :return: The image as bytes object
        """
        return self.encode("jpg", quality, **params)

    def to_ascii(self, max_width=80, **params) -> str:
        """
        Converts the image to ASCII, e.g. to add a coarse preview to
        a log file... or just 4 fun ;-).

        :param max_width: The maximum count of characters per row
        :return: The ASCII image as string
        """
        from .ascii_image import AsciiImage
        return AsciiImage(self, max_width=max_width, **params).get_ascii()

    def to_ipython(self, filetype="png", quality: int = 90, **params) -> Any:
        """
        Converts the image to it's IPython representation, e.g. to allow
            faster visualization via using JPG.

        :param filetype: The file type such as "png" or "jpeg"
        :param quality: The compression level
        :param params: Advanced encoding params. See :meth:`encode`
        :return: The IPython.display.Image
        """
        from IPython.display import Image as IPImage
        return IPImage(self.encode(filetype=filetype, quality=quality,
                                   **params))

    def save(self, target: str, **params):
        """
        Saves the image to disk

        :param target: The storage target such as a filename
        :keyword int quality: The image quality between (0 = worst quality) and
            (95 = best quality). >95 = minimal loss
        :param params: See :meth:`~encode`
        :return: True on success
        """
        with open(target, "wb") as output_file:
            extension = os.path.splitext(target)[1]
            data = self.encode(filetype=extension, **params)
            output_file.write(data)
            return data is not None

    def is_transparent(self) -> bool:
        """
        Returns if the image is transparent, either alpha transparent or
        color keyed.

        :return: True if the image is transparent
        """
        return (self.pixel_format == PixelFormat.BGRA or
                self.pixel_format == PixelFormat.RGBA)

    def get_raw_data(self) -> bytes:
        """
        Returns the image's raw pixel data as flattened byte array

        :return: The image's pixel data
        """
        return self.to_pil().tobytes()

    def get_hash(self) -> str:
        """
        Returns an image uniquely identifying it

        :return: The image's hash
        """
        return hashlib.md5(self.to_pil().tobytes()).hexdigest()


__all__ = ["Image", "ImageSourceTypes"]
