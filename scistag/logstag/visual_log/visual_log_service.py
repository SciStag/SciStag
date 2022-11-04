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
    Hosts the VisualLog as web service and enables the user to interact with
    the data.
    """

    def __init__(self, log: VisualLog):
        """
        :param log: Defines the log which is being hosted
        """
        self.log = log
        "The log we are hosting"

    def trigger_event(self, *args, **params):
        """
        Is called when an event is triggered.

        Adds the event the log's event list and handled it upon the next
        re-execution.

        :param params: The query parameters
        """
        event_name = params.pop("name", "")
        event_type = params.pop("type", "")
        if len(event_name):
            from scistag.logstag.visual_log.log_event import LogEvent
            self.log.add_event(LogEvent(name=event_name,
                                        event_type=event_type))
            return "OK"
        return "Bad request", 400

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
