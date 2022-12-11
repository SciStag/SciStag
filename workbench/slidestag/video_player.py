from __future__ import annotations
from typing import TYPE_CHECKING
from scistag.imagestag import Color, Image
from scistag.slidestag import Widget, PaintEvent, TapEvent
from scistag.mediastag import VideoSourceMovie

if TYPE_CHECKING:
    from scistag.slidestag.widget import Widget

# VideoPlayer widget creation parameters
VIDEO_PLAYER_AUTO_PLAY = "autoPlay"
"Automatically start playing upon creation?"
VIDEO_PLAYER_AUTO_SIZE = "autoSize"
"Automatically enlarge the view to the size of the video?"
VIDEO_PLAYER_REPEAT = "repeat"
"Auto-repeat the video when it ended?"
VIDEO_PLAYER_VIDEO_SOURCE = "videoSource"
"Any type of VideoSource object"
VIDEO_PLAYER_VIDEO = "video"
"Path to video data such as a file"
VIDEO_PLAYER_BACKGROUND_COLOR = "backgroundColor"
"The videos' background color. Black by default"
VIDEO_PLAYER_PLAYBACK_SPEED = "playbackSpeed"
"The player's playback speed"


class VideoPlayer(Widget):
    """
    Widget is the base class for visual controls.
    """

    def __init__(self, parent: Widget | None, parameters: dict):
        """
        Initializer

        :param parent: The parent widget
        :param parameters: The parameters
        """
        super().__init__(parent, parameters)
        self.video_source = None
        self._playback_speed = parameters.get(VIDEO_PLAYER_PLAYBACK_SPEED, 1.0)
        "The playback speed in the relation to the original"
        self.auto_size = parameters.get(VIDEO_PLAYER_AUTO_SIZE, True)
        self.auto_play = parameters.get(VIDEO_PLAYER_AUTO_PLAY, True)
        self._repeat = parameters.get(VIDEO_PLAYER_REPEAT, False)
        self.background_color: Color = parameters.get(
            VIDEO_PLAYER_BACKGROUND_COLOR, Color(0, 0, 0, 255)
        )
        if isinstance(self.background_color, tuple):
            self.background_color = Color(*self.background_color)
        self.last_image = None  # The last video image frame
        self.image_update_timestamp = 0.0
        "Timestamp of the last image update"
        if VIDEO_PLAYER_VIDEO in parameters:
            self.video_source = VideoSourceMovie(
                parameters[VIDEO_PLAYER_VIDEO], self.get_session().get_media_paths()
            )
            self.handle_video_loaded()
        elif VIDEO_PLAYER_VIDEO_SOURCE in parameters:
            self.video_source = parameters[VIDEO_PLAYER_VIDEO_SOURCE]
            self.handle_video_loaded()
        self.video_source.auto_progress = False
        self.video_source.repeat = self._repeat
        self.video_source.speed = self._playback_speed

    def set_playback_speed(self, value: float):
        """
        Sets the playback speed in percent

        :param value: The new speed value (1.0 = 100% of the normal speed, 2.0 = two times as fast)
        """
        self._playback_speed = value
        self.video_source.speed = value

    def set_repeat(self, value: bool):
        """
        Sets if repeat mode is enabled or not

        :param value: The new mode
        """
        self._repeat = value
        self.video_source.repeat = value

    def get_repeat(self) -> bool:
        """
        Returns if the repeat mode is enabled

        :return: The state
        """
        return self._repeat

    def get_playback_speed(self) -> float:
        """
        Returns the playback speed factor, 1.0 = original speed

        :return: The speed in percent
        """
        return self._playback_speed

    def handle_video_loaded(self) -> bool:
        """
        Called when the video changed and was successfully loaded
        """
        if self.auto_size:
            self.set_size(self.video_source.video_size)
        if self.auto_play:
            self.video_source.start()
        return True

    def handle_paint(self, event: PaintEvent) -> bool:
        """
        Is called when ever the view shall be painted

        :param event: The paint event containing information about the target canvas and other required parameters
            to paint the current widget.
        :return: True if the execution shall continue
        """
        canvas = event.canvas
        # theme = self.get_theme()
        width, height = self.size()
        if self.video_source.update_progress():  # TODO To be moved to a timer
            self.repaint()
            self.image_update_timestamp, next_frame = self.video_source.get_image(
                self.image_update_timestamp
            )
            if next_frame is not None:
                next_frame: Image
                if (
                    width != next_frame.width or height != next_frame.height
                ):  # resizing required?
                    max_scale = min(
                        width / next_frame.width, height / next_frame.height
                    )
                    tar_width = int(next_frame.width * max_scale)
                    tar_height = int(next_frame.height * max_scale)
                    self.last_image = next_frame.resized((tar_width, tar_height))
                else:
                    self.last_image = next_frame

        if self.video_source.valid and self.last_image is not None:
            if width != self.last_image.width or height != self.last_image.height:
                if self.background_color.to_int_rgba()[3] != 0:
                    canvas.rect(
                        pos=(0.0, 0.0),
                        size=self.size,
                        color=self.background_color,
                        outline_color=Color(0, 0, 0),
                        outline_width=0,
                    )
            canvas.draw_image(
                self.last_image,
                (
                    width // 2 - self.last_image.width // 2,
                    height // 2 - self.last_image.height // 2,
                ),
            )
        else:
            if self.background_color.to_int_rgba()[3] != 0:
                canvas.rect(
                    pos=(0.0, 0.0),
                    size=self.size,
                    color=self.background_color,
                    outline_color=Color(0, 0, 0),
                    outline_width=0,
                )

        if not super().handle_paint(event):
            return False
        return True

    def handle_click(self, event: TapEvent) -> bool:
        """
        Is called when a mouse click or touch is executed

        :param event: The tap event containing information about the location of the tap
        :return: True if the execution shall continue
        """
        if not super().handle_click(event):
            return False
        return True

    def handle_load(self) -> bool:
        """
        Called when the widget becomes visible and shall be loaded

        :return: If it's true the view shall be loaded
        """
        super().handle_load()
        return True

    def handle_unload(self) -> bool:
        """
        Called when the widget becomes invisible and shall be unloaded

        :return: The previous state. If it's fall the unload can be skipped
        """
        super().handle_unload()
        return True


__all__ = [
    "VideoPlayer",
    "VIDEO_PLAYER_VIDEO",
    "VIDEO_PLAYER_AUTO_PLAY",
    "VIDEO_PLAYER_REPEAT",
    "VIDEO_PLAYER_AUTO_SIZE",
    "VIDEO_PLAYER_VIDEO_SOURCE",
    "VIDEO_PLAYER_BACKGROUND_COLOR",
]
