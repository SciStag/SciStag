"""
The ImageStag module provides a large set of image creation, manipulation and
analysis methods by combining the
strengths of the well known libraries PILLOW, OpenCV and scikit-image.
"""

from .definitions import ImsFramework, PIL, PIL_AVAILABLE, cv, opencv_available
from .bounding import Bounding2D, Bounding2DTypes
from .pos2d import Pos2D, Pos2DTypes
from .size2d import Size2D, Size2DTypes
from .image import Image
from .pixel_format import PixelFormat
from .interpolation import InterpolationMethod
from .image_filter import ImageFilter
from .color import Color, Colors, ColorTypes
from .canvas import Canvas
from .font import Font, HTextAlignment, VTextAlignment
from .anchor2d import Anchor2D, Anchor2DTypes

__all__ = ["Bounding2D", "Color", "ColorTypes", "Colors",
           "ImsFramework", "Image", "ImageFilter",
           "cv", "opencv_available",
           "PIL", "PIL_AVAILABLE",
           "Canvas", "Font", "HTextAlignment", "VTextAlignment",
           "Size2D", "Size2DTypes", "Pos2D", "Pos2DTypes",
           "Anchor2D", "Anchor2DTypes"]
