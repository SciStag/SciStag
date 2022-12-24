"""
A demo which shows how to host a log via http and how to update it's content
continuously using a callback.
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
    def update_image(self):
        self.frame_timestamp, new_image = self.video_source.get_image(
            self.frame_timestamp
        )
        if new_image is not None:
            # new image available? normalize it's size to ~1 Megapixel
            self.last_image = new_image.resized_ext(max_size=(1024, 1024))
        if self.last_image is not None:
            self.image(self.last_image, "LiveView", filetype=("jpg", 80))
            self.br().log_statistics()
        else:
            self.log("Did not receive any image yet :(")


if VisualLog.is_main():
    FRAME_RATE = 60.0  # update as fast as possible
    test_log = VisualLog(
        "Webcam Demo",
        refresh_time_s=1.0 / FRAME_RATE,
        start_browser=os.environ.get("DEMO_VISLOG_BROWSER", "1") == "1",
    )
    test_log.run_server(
        continuous=False,  # update continuously
        auto_clear=False,  # clear log for us each turn
        url_prefix="/webcamDemo",  # host at /webCamDemo
        builder=LiveCameraDemo,
    )  # our update func
