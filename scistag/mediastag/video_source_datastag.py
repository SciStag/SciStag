from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.datastag import DataStagConnection
import numpy as np

from scistag.imagestag import Image
from scistag.mediastag import VideoSource


class VideoSourceDataStag(VideoSource):
    """
    A video source which streams video data directly from a DataStag vault
    """

    def __init__(self, connection: DataStagConnection | None, data_path: str):
        """
        :param connection: The connection from which the image is received.
            The local connection by default
        :param data_path: The data path within the connection
        """
        super().__init__()
        from scistag.datastag.data_stag_connection import DataStagConnection

        self.connection: DataStagConnection = (
            connection if connection else DataStagConnection(local=True)
        )
        self.data_path = data_path
        self.is_stream = True
        self.last_image: Image | None = None
        self.video_resolution = (1920, 1080)
        if self.update_progress() and self.valid:
            self.video_resolution = self.last_image.get_size()

    def update_progress(
        self,
    ) -> bool:
        """
        Tries to update the videos' progress

        :param repeat: Defines if the video shall repeat when the end is reached
        :param speed: The speed factor
        :return: True if the progress was updated
        """
        super().update_progress()
        old_ts = self.last_update_timestamp
        new_ts, _ = self._get_image_int(self.last_update_timestamp)
        return old_ts != new_ts

    def handle_datastag_image_changed(self):
        """
        Called when ever the image changed
        """
        self.video_resolution = self.last_image.get_size()

    def _get_image_int(
        self, timestamp: float | None = None
    ) -> tuple[float, Image | None]:
        if self.start_timestamp == 0.0:
            if self.last_update_timestamp == timestamp:
                return self.last_update_timestamp, None
            else:
                return self.last_update_timestamp, self.last_image
        new_timestamp, new_data = self.connection.get_ts_modified(
            self.data_path, timestamp=timestamp
        )
        if new_data is None:
            return timestamp, None
        self.last_update_timestamp = new_timestamp
        self.valid = True
        if not isinstance(new_data, np.ndarray):
            self.last_image = Image(new_data)
            self.handle_datastag_image_changed()
            return new_timestamp, self.last_image
        self.last_image = Image(new_data)
        return new_timestamp, self.last_image
