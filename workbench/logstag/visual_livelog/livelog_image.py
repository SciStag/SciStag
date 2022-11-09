"""
Implements the class :class:`LiveLogImage` which renders an image to a
VisualLiveLog.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from scistag.imagestag import Image
from scistag.logstag.visual_livelog import LogWidget

if TYPE_CHECKING:
    from scistag.vislog import VisualLiveLog


class LogImage(LogWidget):
    """
    Defines an image widget which is displayed in the visual live log
    """

    def __init__(self, log: "VisualLiveLog"):
        """
        :param log: The log to which this widget belongs
        """
        super().__init__(log)
        self.image: Image | None = None

    def update_image(self, image: Image | None):
        """
        Updates the image and refreshes the live log

        :param image: The new image or None to disable the widget
        """
        mlfs = self.log.max_live_fig_size
        if (image is not None and
                (image.width > mlfs.width or
                 image.height > mlfs.height)):
            self.image = image.resized_ext(max_size=mlfs)
        else:
            self.image = image
        self.log.handle_widget_modified(self)

    def write(self):
        if self.image is not None:
            self.log.image(self.image, "liveLogImage")

    def __bool__(self):
        return super().__bool__() and self.image is not None
