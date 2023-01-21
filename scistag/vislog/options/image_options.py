"""
Defines image specific logging options such as the (default) image format and quality
"""

from __future__ import annotations

from typing import Union

from pydantic import BaseModel

from scistag.imagestag import Size2DTypes


class ImageOptions(BaseModel):
    """
    Image and figure default configurations
    """

    class Config:
        arbitrary_types_allowed = True

    embed_images: Union[bool, None] = (None,)
    """Defines if images shall be directly embedded into
        the HTML log instead of being stored as separate files.

        By default True if Markdown is not set as one of the "formats_out",
        otherwise False by default as Markdown will need the files on disk."""
    default_filetype: Union[tuple[str, int]] = ("png", 90)
    """The default output image and figures format qnd quality.

        Alternatively "jpg" or "bmp" can be used (to minimize the bandwidth
        or in the later case if you are the intranet w/ unlimited bandwidth
        and want to host it live at maximum performance)."""
    max_fig_size: Union[Size2DTypes, None] = None
    """The optimum, maximum width and height for embedded figures and images"""
    log_images: bool = True
    """Defines if images shall be logged"""

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
        from scistag.imagestag import Size2D

        if self.max_fig_size is not None and not isinstance(self.max_fig_size, Size2D):
            self.max_fig_size = Size2D(self.max_fig_size)
        else:
            self.max_fig_size = Size2D(1024, 1024)
