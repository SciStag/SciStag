"""
Implements the class :class:`LogServiceExtension` which allows the hosting of
individual files and services
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Callable

import filetype
from pydantic import BaseModel

from scistag.filestag import FileStag, FilePath
from scistag.vislog import BuilderExtension
from scistag.webstag.server import WebRequest, WebResponse


@dataclass
class PublishingInfo:
    """
    Contains information about the just published file and how to access it externally
    """

    relative_url: str
    """The published object's relative URL"""


class LogServiceExtension(BuilderExtension):
    """
    The service extension allows the publishing of individual files and web services.

    It also allows the registration of additional JavaScript and CSS files which
    will automatically embedded in the result log files.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.static_files: dict[str, bytes | str] = {}
        "Statically hosted files for a pure web based provision of the log"
        self.services: dict[str, Callable] = {}
        "List of services hosted by this log"
        self.css_sources: dict[str, str] = {}
        "Dictionary of additional CSS file sources"
        self.js_sources: dict[str, str] = {}
        "Dictionary of additional JavaScript sources"
        self.publish("vl_upload_file", self.handle_file_upload)

    def publish(
            self,
            path: str,
            content: bytes | str | Callable[[WebRequest], WebResponse],
            store: bool | None = None,
    ) -> PublishingInfo:
        """
        Provides a data file relative to the current log / website location.

        If the log is configured to log its content to disk this function will also
        store the data next to the log by default. Otherwise the file can be accessed
        via the URLs provided in the publishing result returned.

        :param path: The path at which the data or service shall be provided
        :param content: The file's content (if provided as bytes string) or the file's
            absolute path or a service to be called.
        :param store: Defines if the data shall also be stored to disk.

            By default if the log is stored to disk and not dynamic, e.g. no callback
            function, custom service class etc. also all published files be stored to
            disk as well.
        """
        if isinstance(content, Callable):
            self.services[path] = content
        self.static_files[path] = content
        if isinstance(content, str):
            if not FilePath.exists(content):
                raise FileNotFoundError(f"Published file {content} not found")
        if store is None and self.page_session.log_to_disk:
            store = True
        if store and isinstance(content, (bytes, str)):
            if isinstance(content, str):
                content = FileStag.load(content)
            # store the file also on disk if the log is stored to disk
            FilePath.make_dirs(
                FilePath.dirname(self.page_session.target_dir + "/" + path),
                exist_ok=True,
            )
            if self.builder.options.output.log_to_disk and not \
                    self.builder.options.output.single_file:
                FileStag.save(self.page_session.target_dir + "/" + path, content)
        info = PublishingInfo(relative_url=path)
        return info

    def get_file(self, filename: str) -> WebResponse | None:
        """
        Tries to receive a file created by this log, either stored locally
        or in memory via :meth:`add_static_file`.

        :param filename: The file's name
        :return: The file's content (if available)
        """
        data = None
        if filename in self.static_files:
            data = self.static_files[filename]
            if isinstance(data, str):
                data = FileStag.load(data)
        if data is None:
            abs_filename = os.path.abspath(
                self.page_session.target_dir + "/" + filename
            )
            if not abs_filename.startswith(self.page_session.target_dir):
                return None
            data = FileStag.load(abs_filename)
        if data is None:
            return None

        response = WebResponse(body=data)

        mime_types = {
            ".css": "text/css",
            ".htm": "text/html",
            ".html": "text/html",
            ".json": "application/json",
        }

        extension = FilePath.split_ext(filename)[1]
        if extension in mime_types:
            response.mimetype = mime_types[extension]

        if response.mimetype is None:
            ft = filetype.guess(response.body)
            if ft is not None:
                response.mimetype = ft.mime

        return response

    def handle_web_request(self, request: WebRequest) -> WebResponse | None:
        """
        Is called when the request wasn't handled otherwise

        :param request: The web request
        :return: The response
        """
        if request.path == "live":
            return self.get_file("liveView.html")
        if request.path in self.services:
            return self.services[request.path](request)
        return self.get_file(request.path)

    def register_js(self, name: str, path: str):
        """
        Registers an additional JavaScript file which shall be loaded from the log.

        The data needs to be published via :meth:`publish` prior registering it.

        :param name: A unique identifier of the script added to distinguish it
        :param path: The path as passed to :meth:`publish`.
        """
        self.js_sources[name] = path

    def register_css(self, name: str, path: str):
        """
        Registers an additional CSS file which shall be loaded from the log.

        The data needs to be published via :meth:`publish` prior registering it.

        :param name: A unique identifier of the script added to distinguish it
        :param path: The path as passed to :meth:`publish`.
        """
        self.css_sources[name] = path

    def get_embedding_code(self, static: bool = False) -> str:
        """
        Returns the embedded code which needs to be stored at the beginning of a new
        html file to load all Cascading Style Sheets and JavaScripts registered
        in this service.

        :param static: Defines if all elements shall be embedded into the output file
        :return: The HTML code
        """
        css = ""
        js = ""
        if static:
            for key, path in self.css_sources.items():
                content = self.get_file(path).body.decode("utf-8")
                css += f'<style>{content}</style>'
            for key, path in self.js_sources.items():
                content = self.get_file(path).body.decode("utf-8")
                js += f'<script>{content}</script>\n'
        else:
            for key, path in self.css_sources.items():
                css += f'<link rel="stylesheet" type="text/css" href="{path}"/>\n'
            for key, path in self.js_sources.items():
                js += f'<script src="{path}"></script>\n'
        return css + js

    def handle_file_upload(self, request: WebRequest):
        """
        File upload handler which is called when a file is uploaded

        :param request: The upload request
        :return: The response
        """
        widget_name = request.form.get("widget", "")
        if widget_name == "":
            return WebResponse(status=400, body=b"Error")
        widgets = self.builder.widget.find_all_widgets()
        if widget_name not in widgets:
            return WebResponse(status=400, body=b"Error - unknown target")

        widget = widgets[widget_name]
        from scistag.vislog.widgets import LFileUpload

        if not isinstance(widget, LFileUpload):
            return WebResponse(status=400, body=b"Error - invalid widget")
        widget.handle_file_upload(request)

        return WebResponse(status=200, body=b"OK")
