"""
A demo which shows how to visualize a live camera stream inside a log.
"""
from __future__ import annotations
import os

from scistag.vislog import VisualLog, VisualLogBuilder, cell


class LiveCameraDemo(VisualLogBuilder):
    """
    A simple demo which shows the live image of your first USB camera in your
    browser.
    """

    def __init__(self, **kwargs):
        """
        Initializer
        """
        super().__init__(**kwargs)
        from scistag.mediastag.camera_cv2 import CameraCv2

        # Initialize first USB camera (change by your needs)
        self.video_source = CameraCv2(0)
        # Start camera (runs in a background thread)
        self.video_source.start()
        self.frame_timestamp = 0.0
        self.last_image = None

    @cell
    def header(self):
        self.title(f"Webcam Demo")

    @cell(interval_s=1.0 / 160, continuous=True)
    def live_image_view(self):
        # try to fetch the newest image from the stream
        self.frame_timestamp, new_image = self.video_source.get_image(
            self.frame_timestamp
        )
        # new image available? normalize it's size to ~1 Megapixel
        if new_image is not None:
            self.last_image = new_image.resized_ext(max_size=(1024, 1024))
        # every received any image yet?
        if self.last_image is None:
            self.log("Did not receive any image yet :(")
            return
        self.image(self.last_image, "LiveView", filetype=("jpg", 80))
        # TODO Statistics moved to cell and need to be updated
        self.br().log_statistics()


if VisualLog.is_main():
    test_log = VisualLog("Webcam Demo").run_server(builder=LiveCameraDemo)
