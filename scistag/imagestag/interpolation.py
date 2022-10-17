"""
Defines the different interpolation and rescaling methods supported by
ImageStag.
"""

from __future__ import annotations

from enum import Enum

import PIL.Image


class InterpolationMethod(Enum):
    """
    Enumeration of image interpolation methods
    """

    NEAREST = 0
    """
    The pixel will be kept intact, the upscaled image has quite hard pixel edges 
    and the downscaled image is noisy
    """
    LINEAR = 1
    """
    Linear interpolation. Mixes up to four colors based upon subpixel position.
    """
    CUBIC = 2
    """
    Cubic interpolation. Matches the pixels of the source region to the image 
    region and tries to preserve contours
    """
    LANCZOS = 3
    """
    The highest image rescaling quality available in cv2/PIL. Use this if
    performance is not the most important
    """

    def to_cv(self):
        """
        Maps the enum to the corresponding OpenCV type

        :return: The OpenCV constant
        """

        class Definitions:
            """
            Definition of mappings from SciStag.Image to OpenCV
            """
            cv2_interpolation_mapping = {
                self.NEAREST: 6,  # INTER_NEAREST_EXACT,
                self.LINEAR: 1,  # INTER_LINEAR,
                self.CUBIC: 2,  # INTER_CUBIC
                self.LANCZOS: 4  # INTER_LANCZOS4
            }

        return Definitions.cv2_interpolation_mapping[self]

    def to_pil(self):
        """
        Maps the enum to the corresponding PIL type

        :return: The PIL constant
        """

        class Definitions:
            """
            Definition of mappings from SciStag.Image to PIL
            """
            pil_interpolation_mapping = {
                self.NEAREST: PIL.Image.Resampling.NEAREST,
                self.LINEAR: PIL.Image.Resampling.BILINEAR,
                self.CUBIC: PIL.Image.Resampling.BICUBIC,
                self.LANCZOS: PIL.Image.Resampling.LANCZOS
            }

        return Definitions.pil_interpolation_mapping[self]
