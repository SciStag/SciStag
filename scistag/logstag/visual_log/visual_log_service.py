"""
Implements the class :class:`VisualLogService` which provides a logs
content via http.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.logstag.visual_log import VisualLog


class VisualLogService:
    """
    Provides the log as a WebService
    """

    def __init__(self, log: VisualLog):
        """
        :param log: Defines the log which is being hosted
        """
        self.log = log
        "The log we are hosting"

    def get_index(self) -> bytes:
        """
        Returns the most recent index.html
        """
        return self.log.get_page("html")

    def get_pid(self):
        """
        Returns the log's process id
        :return: The log's process ID
        """
        return f"{os.getpid()}"

    def live(self):
        """
        Returns the most recent liveView.html
        :return:
        """
        return self.log.get_file("liveView.html")
