"""
A demo which shows how to visualize a live camera stream inside a log.
"""
from __future__ import annotations

from scistag.mediastag.camera_cv2 import CameraCv2
from scistag.vislog import VisualLog, LogBuilder, stream, section


class LiveCameraDemo(LogBuilder):
    """
    A simple demo which shows the live image of your first USB camera in your
    browser.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timestamp = 0.0
        self.camera = CameraCv2(0).start()

    @stream(interval_s=1.0 / 60.0, continuous=True)
    def process_new_image(self):
        # try to fetch the newest image from the stream
        self.timestamp, new_image = self.camera.get_image(self.timestamp)
        # new image available? normalize it's size to ~1 Megapixel
        if new_image is not None:
            self["image"] = new_image.resized_ext(max_size=(1024, 1024))

    @section("Webcam Demo", requires="image")
    def live_image_view(self):
        self.image(self["image"], "LiveView", filetype=("jpg", 80))
        self.br(2).live_image_view.cell.log_statistics()


if VisualLog.is_main():
    test_log = VisualLog("Webcam Demo").run_server(builder=LiveCameraDemo)
