"""
A demo which shows how to host a log via http and how to update it's content
continuously using a callback.
"""

from scistag.logstag.visual_log import VisualLog


class LiveCameraDemo:
    """
    A simple demo which shows the live image of your first USB camera in your
    browser.
    """

    def __init__(self):
        """
        Initializer
        """
        from scistag.mediastag.camera_cv2 import CameraCv2
        # Initialize first USB camera (change by your needs)
        self.camera = CameraCv2(0)
        # Start camera (runs in a background thread)
        self.camera.start()
        self.frame_timestamp = 0.0
        self.image = None

    def update_function(self, vl: VisualLog):
        """
        Is called at the defined refresh_time_s interval
        :param vl:  The log handle
        """
        vl.title(f"Webcam Demo")
        self.frame_timestamp, new_image = \
            self.camera.get_image(self.frame_timestamp)
        if new_image is not None:
            # new image available? normalize it's size to ~1 Megapixel
            self.image = new_image.resized_ext(max_size=(1024, 1024))
        if self.image is not None:
            vl.image(self.image, "LiveView")
        else:
            vl.log("Did not receive any image yet :(")
        vl.log("")
        vl.log_statistics()

    @classmethod
    def start(cls):
        """
        Setups the log and starts the web server afterwards
        """
        frame_rate = 60.0  # update as fast as possible
        test_log = VisualLog("Webcam Demo",
                             log_to_disk=False,  # no need, we host via a server
                             refresh_time_s=1.0 / frame_rate,
                             image_format="jpg",  # we mainly work with photos
                             image_quality=80)
        view = cls()  # create object instance
        test_log.run_server(continuous=True,  # update continuously
                            host_name="0.0.0.0",  # host on all adapters
                            mt=True,  # required for continuous hosting
                            auto_clear=True,  # clear log for us each turn
                            url_prefix="/webcamDemo",  # host at /webCamDemo
                            builder=view.update_function)  # our update func


if __name__ == "__main__":
    LiveCameraDemo.start()
