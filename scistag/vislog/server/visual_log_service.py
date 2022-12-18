"""
Implements the class :class:`VisualLogService` which provides a logs
content via http.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from scistag.vislog.visual_log import HTML
from scistag.webstag.server import WebResponse

if TYPE_CHECKING:
    from scistag.vislog import VisualLog


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
            from scistag.vislog.widgets.log_event import LEvent

            self.log.add_event(LEvent(name=event_name, event_type=event_type))
            return "OK"
        return "Bad request", 400

    def get_index(self) -> bytes:
        """
        Returns the most recent index.html
        """
        return self.log.default_page.get_body(format_type=HTML)

    def get_elements(self, *path, timestamp: int = 0) -> WebResponse:
        """
        Returns the page's element at given element path inside ._logs
        """
        try:
            timestamp = int(timestamp)
        except TypeError:
            pass
        new_timestamp, body = self.log.get_element(
            name="-".join(path), output_format=HTML, backup=True
        )
        new_timestamp -= self.log.start_time
        new_timestamp = int(round(new_timestamp * 1000))
        if new_timestamp == timestamp:  # nothing changed?
            return WebResponse(body=b"", status=304)
        response = WebResponse(body=body, headers={"timestamp": new_timestamp})
        return response

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
