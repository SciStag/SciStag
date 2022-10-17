from __future__ import annotations
import time

from scistag.imagestag import Image, ImageFilter


class VideoSource:
    """
    Defines an arbitrary video source
    """

    def __init__(self):
        """
        Initializer
        """
        self.duration = 0.0
        "The video's overall duration in seconds. 0 if a stream"
        self.is_stream = False
        "Defines if the source is a continuous stream"
        self.start_timestamp = 0.0
        "Timestamp when the playback started or continued"
        self.last_update_timestamp = 0.0
        "Timestamp of the last update"
        self.position = 0.0
        "The current position (in seconds)"
        self.valid = False
        "Defines if there is a valid source"
        self.video_resolution = (1, 1)
        "The video's size in pixels"
        self.fps = 1.0
        "The videos frame per second count"
        self.time_per_frame = 1.0
        "The amount of seconds per frame (1/fps)"
        self.image_filter: ImageFilter | None = None
        "A filter which shall be applied to every image received from the video before it's returned"
        self.last_raw_image: Image | None = None
        "The last raw image received internal"
        self.last_raw_image_timestamp: float = 0.0
        "The last raw image's time stamp"
        self.last_returned_image: Image | None = None
        "The last returned image (after applying filters etc.)"
        self.speed = 1.0
        "The movie's playback speed. 1.0 = 100%"
        self.repeat = True
        "The movie's repeat mode"
        self.time_function = lambda: time.time()
        self.auto_progress = True
        "If defined the get_image function is also allowed to update the video's progress. Otherwise the managing \
        control, e.g. the VideoPlayer is responsible to do so"

    def start(self):
        """
        Starts the video
        """
        self.position = 0.0
        self.last_update_timestamp = self.start_timestamp = self.time_function()

    def stop(self):
        """
        Stops the video
        """
        self.position = 0.0
        self.start_timestamp = 0.0

    def pause(self):
        """
        Pauses the video
        """
        self.start_timestamp = 0.0

    def continue_video(self):
        """
        Pauses the video
        """
        self.last_update_timestamp = self.start_timestamp = self.time_function()

    def seek(self, position_s: float) -> float:
        """
        Seeks to given video position
        :param position_s: The new desired position
        :return: The real new position
        """
        position_s = min([max([0, position_s]), self.duration])
        self.position = position_s
        self.last_update_timestamp = self.time_function()
        return self.position

    def set_filter(self, image_filter: ImageFilter | None) -> None:
        """
        Assigns a filter which is assigned to every image received from the original video source. For example
        call set_filter(Grayscale()) to convert the camera or video to grayscale. You can also assign an
        ImageFilterPipeline to combine multiple filters.
        :param image_filter: The filter to assign or None to disable it
        """
        self.image_filter = image_filter

    def update_progress(self) -> bool:
        """
        Tries to update the videos' progress
        :param repeat: Defines if the video shall repeat when the end is reached
        :param speed: The speed factor
        :return: True if the progress was updated
        """
        if self.is_stream:
            return False
        cur_time = self.time_function()
        if cur_time - self.last_update_timestamp < self.time_per_frame / self.speed:
            # do nothing if not even a frame changed
            return False
        if self.start_timestamp != 0.0 and self.position != self.duration:
            time_diff = cur_time - self.last_update_timestamp
            new_pos = self.position + time_diff * self.speed
            self.last_update_timestamp = cur_time
            self.seek(new_pos)
            if self.position == self.duration and self.repeat:
                self.seek(0.0)
            return True
        return False

    def _get_image_int(self, timestamp: float | None = None) -> tuple[
        float, Image | None]:
        """
        Returns the current image as np array (internal function providing the raw data before filters
        etc. are applied)
        :param timestamp: The timestamp of the last image received
        :return: Updated timestamp, the image
        """
        return timestamp, None

    def get_image(self, timestamp: float | None = None, wait: bool = False,
                  timeout_s: float = 2.0) -> tuple[float, Image | None]:
        """
        Returns the current image as np array

        :param timestamp: The timestamp of the last image received
        :param wait: If set the function will wait for the next valid image
        :param timeout_s: The timeout in seconds before a TimeoutError
            exception will be raised. 2 seconds by default. If set to -1
            the function will wait forever.
        :return: Updated timestamp, the image
        """
        if self.auto_progress:
            self.update_progress()
        new_timestamp, new_image = self._get_image_int(timestamp)
        if new_timestamp != self.last_raw_image_timestamp and new_image is not None:
            self.last_raw_image = self.last_returned_image = new_image
            if self.image_filter is not None:
                self.last_returned_image = self.image_filter.filter(
                    self.last_raw_image)
            return self.last_raw_image_timestamp, self.last_returned_image
        if wait:
            start_time = time.time()
            while time.time() - start_time < timeout_s or timeout_s == -1.0:
                new_timestamp, image = self.get_image(timestamp, wait=False)
                if image is not None:
                    return new_timestamp, image
            raise TimeoutError("Timeout exceeded")
        return self.last_raw_image_timestamp, None
