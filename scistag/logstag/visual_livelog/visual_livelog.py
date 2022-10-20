"""
The VisualLiveLog class allows the generation and viewing of live HTML reports
which can be viewed live in code editors next to your code using
HTML side views such as PyCharm's Preview function.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import time

from ...filestag import FilePath, FileStag
from ...imagestag import Size2D, Size2DTypes
from ..visual_log.visual_log import VisualLog, HTML
from ..visual_log.sub_log import SubLogLock

if TYPE_CHECKING:
    from .livelog_progress_bar import LiveLogProgress
    from .livelog_image import LiveLogImage
    from .livelog_text import LiveLogText
    from .livelog_widget import LiveLogWidget


class VisualLiveLog(VisualLog):
    """
    The VisualLiveLog class allows the generation and viewing of live HTML
    reports (similar to Jupyter Notebooks) including images, diagrams,
    tables and all you need to dive into your data.
    """

    def __init__(self, target_dir, title, refresh_time_s: float = 0.25,
                 max_fig_size: Size2DTypes | None = None,
                 max_live_fig_size: Size2DTypes | None = None,
                 **params):
        """
        :param target_dir: The directory in which the report shall be stored
        :param title: The log's title
        :param refresh_time_s: The refresh time per frame in seconds
        :param max_fig_size: The optimum, maximum width and height for
            embedded figures and images
        :param max_live_fig_size: The optimum, maximum width and height for
            embedded figures and images in the live preview
        :param params: Additional parameters to be passed on to
            :class:`VisualLog`
        """
        super().__init__(target_dir=target_dir, title=title,
                         refresh_time_s=refresh_time_s,
                         max_fig_size=max_fig_size,
                         **params)
        if max_live_fig_size is None:
            max_live_fig_size = Size2D(400, 400)
        if not isinstance(max_live_fig_size, Size2D):
            max_live_fig_size = Size2D(max_live_fig_size)
        self._max_live_fig_size = max_live_fig_size
        "Defines the width and height for content shown in the live preview"
        self._embed_images = True  # embed by default
        self._image_default_format = "jpg"  # fast image writing by default
        self._md_export = False  # No markdown by default
        self._console_export = True  # Log to console
        self._txt_export = False  # No txt by default
        self._log_txt_images = False  # No text image logging
        self.last_update = 0.0
        "System time in s when the last update was executed (amd finished)"
        self.last_update_start = 0.0
        "System time in s when the last update was started"
        self.effective_fps = 0.0
        "The effective update fps over the last seconds"
        self._effective_fps_check = 0.0
        "Time when the last fps check was executed"
        self._effective_fps_check_frequency = 2.0
        "Time in seconds how often the fps is updates"
        self._frames_since_check = 0
        "Frames / updates executed since last check"
        new_template = \
            FileStag.load_text_file(FilePath.absolute_comb(
                "templates/left_right_layout.html"))
        self._renderers[HTML].set_sub_logs(['liveLog'])
        self._renderers[HTML]. \
            set_body_template(
            new_template,
            live_content_width=int(self._max_live_fig_size.width),
            live_content_height=int(self._max_live_fig_size.height))
        self.widgets: list["LiveLogWidget"] = []
        """
        The widgets which are displayed in the live log area
        """

    def should_update(self) -> bool:
        """
        Returns true as soon as the time when the live log was updated the
        last time is longer ago than the refresh_time_s passed upon
        initialization.

        :return: True if an update should be executed, e.g. by modifying
        widgets and/or handling begin_update manually.
        """
        return time.time() - self.last_update >= self._refresh_time_s

    def begin_update(self, clear: bool = False,
                     blocking=False) -> SubLogLock:
        """
        To be called before starting to update the live log data.

        Usage:

        ..  code-block: Python

            with vl.begin_update() as upd:
                if not upd:
                    continue
                ...

            or

            vl.begin_update()
            ...
            vl.end_update()

        :param clear: Defines if the whole log shall be cleared prior updating
        :param blocking: Defines if the call shall block to keep a guaranteed
            update time per second.
        :return: True if an updated is allowed
        """
        self.last_update_start = time.time()
        if time.time() - self.last_update < self._refresh_time_s:
            if blocking:
                while time.time() - self.last_update < self._refresh_time_s:
                    time.sleep(self._refresh_time_s / 10)
            else:
                return SubLogLock(log=None)
        sll = self.begin_sub_log("liveLog",
                                 max_fig_size=self._max_live_fig_size)
        if clear:
            self.clear_logs()
        return sll

    def emd_update(self):
        """
        Equivalent o end_sub_log - To be called when you entered a
        begin_update_section without a ``with vl.begin_update()...`` statement.
        """
        self.end_sub_log()

    def end_sub_log(self):
        """
        To be called when an update finished and the site shall be updated

        :param force: Force updating the data of the log, e.g. if a very
            long running section finished and an update should definitely
            be published. Use with care.
        :return: True if the update was executed, false if it was denied b/c
            the false return value of begin_update() was ignored
        """
        cur_time = time.time()
        super().end_sub_log()
        if cur_time - self.last_update > self._refresh_time_s:
            self.last_update = self.last_update_start
            self.write_to_disk()
            self._frames_since_check += 1
            self.update_statistics(cur_time)
            return True
        return False

    def update_statistics(self, cur_time):
        """
        Called internally to the statistics once all x seconds

        :param cur_time: The current time
        """
        if cur_time - self._effective_fps_check > \
                self._effective_fps_check_frequency:
            time_diff = cur_time - self._effective_fps_check
            self.effective_fps = self._frames_since_check / time_diff
            self._frames_since_check = 0
            self._effective_fps_check = cur_time

    @property
    def max_live_fig_size(self) -> Size2D:
        """
        Returns the maximum live figure size in pixels
        """
        return self._max_live_fig_size

    def add_widget(self, widget: LiveLogWidget):
        """
        Adds a widget which is then displayed in the log's live log area

        :param widget: The new widget
        """
        self.widgets.append(widget)

    def remove_widget(self, widget: LiveLogWidget):
        """
        Removes given widget
        """
        if widget not in self.widgets:
            raise KeyError("Unknown widget")
        self.widgets.remove(widget)

    def add_image_widget(self) -> "LiveLogImage":
        """
        Adds an image widget which can display an image in the live log area

        :return: The widget handle which can be used to update the image
        """
        from .livelog_image import LiveLogImage
        image_widget = LiveLogImage(self)
        self.add_widget(image_widget)
        return image_widget

    def add_text_widget(self, text: str | None) -> "LiveLogText":
        """
        Adds a text widget which can display text in the live log area

        :param text: The initial text
        :return: The text widget
        """
        from .livelog_text import LiveLogText
        text_widget = LiveLogText(log=self, text=text)
        self.add_widget(text_widget)
        return text_widget

    def add_progress_bar(self, progress: int | float,
                         max_progress: int | float,
                         text: str | None = None) -> "LiveLogProgress":
        """
        Adds a progress bar widget

        :param progress: The current progress, either in percent or the
            item index.
        :param max_progress: The maximum progress, either 1.0 for percent
            or the item count. Pass -1 for an infinite progress
            indicator.
        :param text: Defines the text to be displayed above the progress bar
        :return: The new widget
        """
        from .livelog_progress_bar import LiveLogProgress
        prog_widget = LiveLogProgress(self, progress=progress,
                                      max_progress=max_progress,
                                      text=text)
        self.add_widget(prog_widget)
        return prog_widget

    def add_style(self):
        start_offset = (time.time() / 2 - int(time.time() / 2)) * 360.0
        start_deg, end_deg = f"{int(start_offset)}", f"{(start_offset + 360)}"
        style = f"""<style>
                @-webkit-keyframes spin {{
                    0% {{ -webkit-transform: rotate({start_deg}deg); }}
                    100% {{ -webkit-transform: rotate({end_deg}deg); }}
                }}
                @keyframes spin {{
                    0% {{ transform: rotate({start_deg}deg); }}
                    100% {{transform: rotate({end_deg}deg); }}
                }}</style> """
        self.html(style)

    def handle_widget_modified(self, widget: "LiveLogWidget"):
        """
        Is called from a widget when ever it was modified directly

        :param widget: The widget which was modified
        """
        if not self.begin_update(clear=True):
            return
        self.add_style()
        for widget in self.widgets:
            widget.write()
        self.end_sub_log()
