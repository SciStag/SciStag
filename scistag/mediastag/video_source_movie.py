"""
Implements the :class:`VideoSourceMovie: which allows receiving images from
a video file such as an mp4.
"""

from __future__ import annotations
import os

from .video_source import VideoSource
from ..imagestag import Image


class VideoSourceMovie(VideoSource):
    """
    Provides a video stream from a file source, e.g. an mp4 file
    """

    def __init__(self, filename: str, media_paths: list[str] | None = None):
        """
        :param filename: The video filename
        :param media_paths: The media paths to seek within
        """
        from moviepy.editor import VideoFileClip
        super().__init__()
        valid_path = None
        self.moviepy: "VideoFileClip" = None
        media_paths = [""] if media_paths is None else media_paths
        for path in media_paths:
            cur_path = f"{path}/{filename}" if len(path)>0 else filename
            if os.path.exists(cur_path):
                valid_path = cur_path
        if valid_path is not None:
            self.valid = True
            self.moviepy = VideoFileClip(valid_path)
            self.video_size = self.moviepy.w, self.moviepy.h
            self.duration = self.moviepy.duration
            self.fps = self.moviepy.fps
            self.time_per_frame = 1.0 / self.fps

    def _get_image_int(self, timestamp: float | None = None) -> tuple[
        float, Image | None]:
        """
        Returns the current image as np array

        :return: The image
        """
        if not self.valid:
            return timestamp, None
        return self.last_update_timestamp, Image(
            self.moviepy.get_frame(self.position))
