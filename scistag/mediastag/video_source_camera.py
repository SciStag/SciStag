from __future__ import annotations
from threading import Thread, Event, RLock
from typing import Callable
import abc

import scistag.imagestag

from .video_source import VideoSource
from ..imagestag import Image


class VideoRetrievalThread(Thread):
    """
    A thread for the asynchronous retrieval of images
    """

    def __init__(self, video_source: "VideoSourceCamera"):
        """
        Initializer
        :param video_source:
        """
        super(VideoRetrievalThread, self).__init__()
        self.camera = video_source
        self.kill_event = Event()

    def run(self) -> None:
        self.camera.handle_initialize_camera()
        while not self.kill_event.is_set():
            timestamp, image = self.camera.handle_fetch()
            if image is not None:
                self.camera.set_image(timestamp, image)


class VideoSourceCamera(VideoSource):
    """
    Defines an arbitrary camera streaming source
    """

    LOCAL_CAMERA_STREAM_IDENTIFIER = "streams.cameras.camera_"
    "Local camera, e.g. a webcam connected to the hosting PC directly"

    LOCAL_CAMERA_STREAM_IDENTIFIER_TYPE = ".type"
    "Name definition of the local camera's type"

    def __init__(self):
        super(VideoSourceCamera, self).__init__()
        self.is_stream = True  # Flag as stream
        self._lock = RLock()
        "Access lock"
        self.recent_image: Image | None = None
        "The most recent image"
        self.recent_timestamp: float = 0.0
        "The most recent image's time stamp"
        self.redirections = []
        "Targets the camera image shall be redirected to"
        self.started = False
        "Defines if the remote thread was started"
        self._remote_thread = VideoRetrievalThread(self)
        "The remote thread"
        self.source = ""
        "The camera's source as unique identifier"
        self.video_resolution = (1920, 1080)

    def add_redirect(self, target: str | Callable[[float, Image], None], timeout_s=5.0):
        """
        Redirects the camera's data into a local or remote DataStag storage

        :param target: If a string this is interpreted as a DataStag target
            identifier, otherwise a function to be
        :param timeout_s: The timeout in seconds for how long the local camera
            streams shall be kept in the vault
        called.
        """
        self.redirections.append((target, timeout_s))
        if isinstance(target, str):  # register local camera
            from ..datastag import DataStagConnection

            lc = DataStagConnection(local=True)
            lc.set(
                target + self.LOCAL_CAMERA_STREAM_IDENTIFIER_TYPE,
                str(type(self)) + "/" + str(self.source),
            )

    @classmethod
    def get_local_camera(cls, source: int | str) -> str | None:
        """
        Returns a unique name for a local camera at given source IF the camera
        is also registered and is usable

        :param source: The camera's index or other unique identifier
        :return: The unique identifier if the camera does exist. Otherwise None
        """
        if cls.get_local_camera_exists(source):
            return cls.get_local_camera_name(source)
        return None

    @classmethod
    def get_local_camera_name(cls, source: int | str) -> str:
        """
        Returns a unique name for a local camera at given source

        :param source: The camera's index or other unique identifier
        :return: The unique identifier
        """
        if isinstance(source, int):
            return f"{cls.LOCAL_CAMERA_STREAM_IDENTIFIER}{source:02d}"
        else:
            return f"{cls.LOCAL_CAMERA_STREAM_IDENTIFIER}{source}"

    @classmethod
    def get_local_camera_exists(cls, source: int | str) -> bool:
        """
        Returns if a camera with given source was registered

        :param source: The camera's source name, class specific. Should be
            globally unique
        :return: True if the camera was found
        """
        from ..datastag import DataStagConnection

        lc = DataStagConnection(local=True)
        local_name = (
            cls.get_local_camera_name(source) + cls.LOCAL_CAMERA_STREAM_IDENTIFIER_TYPE
        )
        return lc.exists(local_name)

    def redirect_to_vault(self, index: int):
        """
        Redirects the camera's stream into the vault
        :param index: The internal index
        """
        self.add_redirect(self.get_local_camera_name(index))

    def handle_redirections(self):
        """
        Forwards the new camera image into callback functions and/or database
        targets
        """
        with self._lock:
            redirections = list(self.redirections)
            recent_image = self.recent_image
            recent_timestamp = self.recent_timestamp
        if recent_image is None:
            return
        for entry in redirections:
            element = entry[0]
            timeout = entry[1]
            if isinstance(element, str):
                image = (
                    recent_image
                    if isinstance(recent_image, scistag.imagestag.Image)
                    else Image(recent_image)
                )
                image: scistag.imagestag.Image
                image_data = image.encode(filetype=".png")
                from ..datastag import DataStagConnection

                local_connection = DataStagConnection(local=True)
                local_connection.set_ts(
                    element, image_data, timeout_s=timeout, timestamp=recent_timestamp
                )

    def update_progress(self) -> bool:
        """
        Tries to update the videos' progress

        :return: True if the progress was updated
        """
        super().update_progress()
        old_ts = self.last_update_timestamp
        new_ts, _ = self._get_image_int(self.last_update_timestamp)
        return old_ts != new_ts

    def _get_image_int(
        self, timestamp: float | None = None
    ) -> tuple[float, Image | None]:
        """
        Returns the most recent image and it's time stamp

        :param timestamp: If provided and the image was not modified no image
            will be returned.
        :return: The newest image if one is available and timestamp does not
            match the previous time stamp.
        """
        with self._lock:
            if self.recent_timestamp == timestamp:
                return self.recent_timestamp, None
            return self.recent_timestamp, self.recent_image

    def set_image(self, timestamp: float, image: Image) -> None:
        """
        Updates the current image

        :param timestamp: The timestamp
        :param image: The newest image
        """
        with self._lock:
            self.recent_timestamp = timestamp
            self.recent_image = image
            self.video_resolution = image.get_size()
            self.valid = True
        self.handle_redirections()

    def start(self) -> "VideoSourceCamera":
        """
        Starts the camera

        :return: The camera object
        """
        super().start()
        if not self.started:
            self.started = True
            self._remote_thread.start()
        return self

    def stop(self) -> "VideoSourceCamera":
        """
        Stops the camera thread

        :return: The camera object
        """
        super().stop()
        if self.started:
            self.started = False
            self._remote_thread.kill_event.set()
            self._remote_thread.join()
        return self

    @classmethod
    def get_camera_name(cls, index: int) -> str:
        """
        Returns the global name of a local camera

        :param index: The camera's index
        :return: The identifier under which the camera can be stored in the
            local DataStag vault
        """
        return f"{cls.LOCAL_CAMERA_STREAM_IDENTIFIER}{index:02d}"

    @abc.abstractmethod
    def handle_initialize_camera(self):
        """
        Initializes the camera. Could be executed in another thread, lock data
            accordingly.
        Overwrite this with your initialization code.
        """
        pass

    @abc.abstractmethod
    def handle_fetch(self) -> tuple[float, Image | None]:
        """
        Tries to fetch data from the camera

        :return: The new image on success. None if no new image was available.
        """
        return 0.0, None
