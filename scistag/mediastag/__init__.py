"""
Provides functions for handling media such as camera, video and audio streams
"""

from .video_source import VideoSource
from .video_source_movie import VideoSourceMovie
from .video_source_camera import VideoSourceCamera
from .video_source_datastag import VideoSourceDataStag
from .camera_cv2 import CameraCv2

__all__ = ["VideoSource", "VideoSourceMovie"]
