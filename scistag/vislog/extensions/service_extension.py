"""
Implements the class :class:`LogServiceExtension` which allows the hosting of
individual files and services
"""

from __future__ import annotations
import os
from typing import Callable

from scistag.filestag import FileStag, FilePath
from scistag.vislog import BuilderExtension
from scistag.webstag.server import WebRequest, WebResponse


class LogServiceExtension(BuilderExtension):
    """
    The service extension allows the publishing of individual files and web services
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.static_files: dict[str, bytes | str] = {}
        "Statically hosted files for a pure web based provision of the log"
        self.services: dict[str, Callable] = {}
        "List of services hosted by this log"

    def publish(
        self, path: str, content: bytes | str | Callable[[WebRequest], WebResponse]
    ):
        """
        Provides a file statically, e.g. to provide it via a
            VisualLiveLogServer.

        Multi-thread safe function.

        :param path: The path at which the data or service shall be provided
        :param content: The file's content (if provided as bytes string) or the file's
            absolute path or a service to be called.
        """
        if isinstance(content, Callable):
            self.services[path] = content
        self.static_files[path] = content
        if isinstance(content, str):
            if not FilePath.exists(content):
                raise FileNotFoundError(f"Published file {content} not found")

    def get_file(self, filename: str) -> bytes | None:
        """
        Tries to receive a file created by this log, either stored locally
        or in memory via :meth:`add_static_file`.

        :param filename: The file's name
        :return: The file's content (if available)
        """
        if filename in self.static_files:
            return self.static_files[filename]
        abs_filename = os.path.abspath(self.page_session.target_dir + "/" + filename)
        if not abs_filename.startswith(self.page_session.target_dir):
            return None
        return FileStag.load(abs_filename)

    def handle_web_request(self, request: WebRequest):
        """
        Is called when the request wasn't handled otherwise

        :param request: The web request
        :return: The response
        """
        if request.path == "live":
            return self.get_file("liveView.html")
        return self.get_file(request.path)
