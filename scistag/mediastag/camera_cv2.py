from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import cv2 as cv
import time

from scistag.imagestag import Image
from scistag.mediastag.video_source_camera import VideoSourceCamera


class CameraCv2(VideoSourceCamera):
    """
    A camera source wrapping OpenCV's camera access capabilities
    """

    def __init__(self, source: int | str):
        """
        Initializer

        :param source: The camera source. When a number is passed it will be interpreted as "web cam" index, e.g. 0,
        otherwise it will be handled as gstreamer pipeline definition.
        """
        super().__init__()
        self.source: int | str = source
        self.handle: cv.VideoCapture | None = None

    def handle_initialize_camera(self):
        from scistag.imagestag import cv, opencv_available
        if not opencv_available():
            raise NotImplementedError(
                "OpenCV not installed. See optional packages.")
        if isinstance(self.source, str):
            # if a full pipeline is defined, connect via gstreamer
            self.handle = cv.VideoCapture(self.source, cv.CAP_GSTREAMER)
        else:  # otherwise n00b mode and just select by index
            self.handle = cv.VideoCapture(self.source)

    def handle_fetch(self) -> tuple[float, Image | None]:
        ret, image = self.handle.read()
        if ret:
            return time.time(), Image(image[..., ::-1].copy())
        else:
            return 0.0, None
