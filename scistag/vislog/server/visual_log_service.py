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
        event_type = params.get("type", "")
        if len(event_type):
            self.log.default_page.handle_client_event(**params)
            return "OK"
        return "Bad request", 400

    def get_index(self) -> bytes:
        """
        Returns the most recent index.html
        """
        return self.log.default_page.get_page(format_type=HTML)

    def get_events(self, *path, sessionId: str) -> WebResponse:
        """
        Returns the page's newest events which shall be executed in JavaScript in the
        script liveLog/defaultLive_view.html
        """
        event_header, event_body = self.log.default_page.get_events_js(sessionId)
        if event_body is None:  # nothing changed?
            return WebResponse(body=b"", status=304)
        response = WebResponse(body=event_body, headers=event_header)
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
