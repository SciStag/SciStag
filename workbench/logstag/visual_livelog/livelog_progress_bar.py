"""
Implements the class :class:`LiveLogProgress` which renders a progress bar
or activity indicator to a VisualLiveLog.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from scistag.logstag.vislog.widgets.log_widget import LogWidget

if TYPE_CHECKING:
    from scistag.logstag.vislog import VisualLiveLog


class LogProgress(LogWidget):
    """
    Displays a progress bar in the VisualLiveLog
    """

    def __init__(self, log: "VisualLiveLog",
                 progress=0.0,
                 max_progress=1.0,
                 text: str | None = None):
        """
        :param log: The target log
        :param progress: The current progress, either a discrete value or
            percent
        :param max_progress: The maximum progress, either 1.0 for percent
            or the count of elements to handle. Pass -1 for an infinite
            progress indicator.
        :param text: An info text which can be displayed above the progress
            bar
        """

        super().__init__(log)
        self.cur_progress = progress
        "The current progress"
        self.max_progress = max_progress
        "The maximum progress"
        self.label_text = text
        "The text to be displayed as label before the progress bar"

    def update(self, progress: int | float):
        """
        Updates the progress

        :param progress: The new progress
        """
        self.cur_progress = progress
        self.log.handle_widget_modified(self)

    def write(self):
        value_text = None
        if isinstance(self.max_progress, float) and self.max_progress != -1:
            value = int(round(self.cur_progress * 100))
            max_value = int(round(self.max_progress * 100))
            if self.label_text is not None:
                perc_round = str(round(self.cur_progress * 100, 3))
                value_text = \
                    f"{self.label_text} " \
                    f"({perc_round.rstrip('0').rstrip('.')}%)"
        elif self.max_progress != -1:
            value = self.cur_progress
            max_value = self.max_progress
            if self.label_text is not None:
                value_text = f"{self.label_text} ({value}/{max_value})"
        else:
            value_text = self.label_text
            value = max_value = 0
        label_html = ''
        if value_text is not None:
            label_html = f'<label for="file">{value_text}</label>'

        if self.max_progress == -1:
            self.log.html(
                f'<div class="loader"></div> {label_html}<br><br>')
            #  f'{label_html} <div class="loader"></div><br><br>')
            return
        self.log.html(
            f'{label_html}<br><progress value="{value}" max="{max_value}" '
            f'style="width:100%;height:25px"></progress><br><br>')
