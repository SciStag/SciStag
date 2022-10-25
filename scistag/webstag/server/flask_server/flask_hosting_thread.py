"""
Implements the class :class:`FlaskHostingThread` which runs the Flask service
in a separate thread.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from scistag.common.mt import ManagedThread

if TYPE_CHECKING:
    from scistag.webstag.server.web_stag_server import WebStagServer


class FlaskHostingThread(ManagedThread):
    """
    Executes a Flask server in a separate thread so that it can run in parallel
    to another main application.
    """

    def __init__(self, server: "WebStagServer"):
        """
        :param server: The server to run in this thread
        """
        super().__init__("FlaskServer")
        self.server = server
        from scistag.webstag.server.web_stag_server import WebStagServer
        assert isinstance(server, WebStagServer)

    def run(self) -> None:
        """
        Thread main execution function
        """
        self.server._run_server()
