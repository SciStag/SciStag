"""
Implements the :class:`ColorMapFilter` class which allows converting a single
channel image (such as a gray scale image or a numpy 2d matrix)
to an RGB image using a map of either discrete or blending
colors to visualize these values such as a heat map.
"""

from __future__ import annotations
import numpy as np
from pydantic import BaseModel

from ...common import StagLock
from ..image_filter import ImageFilter, IMAGE_FILTER_IMAGE, \
    Image
from ..pixel_format import PixelFormat
from ...filestag import FileStag, FilePath

COLOR_MAP_VIRIDIS = "viridis"
"The default pyplot map"
COLOR_MAP_INFERNO = "inferno"
"Inferno sequential map"


class ColorMapCategory(BaseModel):
    """
    Defines a single color map category
    """
    name: str
    "The color map group's name"
    maps: list[str]
    "The maps of the color map group"


ColorMapGroupData = list[ColorMapCategory]
""""
Defines a list of color map categories
"""


class ColorMapData(BaseModel):
    """
    Defines the color map data
    """
    categories: ColorMapGroupData
    "The data of each group containing the category's name and the styles"


class ColorMapFilter(ImageFilter):
    """
    Applies a pixelwise color map to a grayscale image or 2D numpy array to
    create images such as heatmaps or false color visualizations.
    """

    _access_lock = StagLock()
    "Shared data access lock"

    _color_map_data: ColorMapData | None = None
    "A list containing all color map groups"

    _color_map_names: set[str] = set()
    "A set containing all valid color map names"

    def __init__(self, normalize=True, color_map: str = COLOR_MAP_VIRIDIS):
        """
        Initializer

        :param normalize: Defines if the grayscale image gets normalized to
            a range from 0..255 before applying the
        :param color_map: The color map to be used. Use one of the provided
            COLOR_MAPS constants or have a look
            at https://matplotlib.org/stable/tutorials/colors/colormaps.html.
        """
        super(ColorMapFilter, self).__init__()
        self.requires_format = PixelFormat.GRAY
        self.normalize = normalize
        self._color_map_name = ""
        self.precise = False
        self._ensure_colormaps()
        if color_map not in self._color_map_names:
            raise ValueError(f"Unknown color map {color_map}")
        self._set_color_map(color_map)
        """
        Defines if the grayscale image gets normalized to a range from 0..255 
        before applying the filter
        """
        self.name = f"colorMap_{self._color_map_name}"

    def _set_color_map(self, color_map_name: str):
        import matplotlib.pyplot as plt
        self.color_map = plt.get_cmap(color_map_name)
        self._color_map_name = color_map_name
        if not self.precise:
            range_table = np.array([[index / 255.0 for index in range(256)]])
            mapped_colors = self.color_map(range_table)
            self.table = (mapped_colors * 255).astype(np.uint8).reshape(
                (256, 4))
        else:
            self.table = None

    def _apply_filter(self, input_data: dict) -> dict:
        org_image = image = input_data[IMAGE_FILTER_IMAGE]
        image: Image
        gray_image = image.get_pixels_gray()
        if self.normalize:
            min_v = np.min(gray_image)
            max_v = np.max(gray_image[gray_image.shape[0] // 3:, :])
            diff = max_v - min_v
            if diff > 0:
                scaling = 255.0 / diff
                gray_image = np.clip(((gray_image - min_v) * scaling), 0,
                                     255).astype(np.uint8)
        if self.table is not None:
            result: np.ndarray = np.dstack(
                [self.table[:, i][gray_image] for i in range(3)])
        else:
            norm_gray_image = gray_image / 255.0
            result: np.ndarray = (self.color_map(norm_gray_image) * 255).astype(
                np.uint8)
        return {
            IMAGE_FILTER_IMAGE: Image(result, framework=org_image.framework)}

    @classmethod
    def get_colormap_categories(cls):
        """
        Returns a list of all available color map categories and their elements

        :return: A list of all available color map groups
        """
        cls._ensure_colormaps()
        return cls._color_map_data.categories

    @classmethod
    def get_colormap_names(cls) -> set[str]:
        """
        Returns a set containing all valid color map names

        :return: The set of names
        """
        cls._ensure_colormaps()
        return cls._color_map_names

    @classmethod
    def _ensure_colormaps(cls):
        """
        Loads the color maps from file if not done so yet
        """
        with cls._access_lock:
            if cls._color_map_data is not None:
                return
            fn = FilePath.absolute_comb("color_maps.json")
            group_data = FileStag.load_json(fn)
            cls._color_map_data = ColorMapData.parse_obj(group_data)
            cls._color_map_names = set()
            for element in cls._color_map_data.categories:
                cls._color_map_names = \
                    cls._color_map_names.union(set(element.maps))


__all__ = ["ColorMapFilter", "COLOR_MAP_VIRIDIS", "COLOR_MAP_INFERNO"]
