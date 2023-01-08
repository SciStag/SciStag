"""
Implements the class :class:`LFileUpload` which allows the user to upload files to
the server.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Union

from pydantic import Field

from scistag.vislog.widgets.log_widget import LWidget
from scistag.vislog.widgets.event import LEvent
from scistag.webstag.server import WebRequest, FileAttachment

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import LogBuilder

FILE_UPLOAD_EVENT_TYPE = "file_upload"
"Defines an event which is risen by a file upload"


@dataclass
class LFileUploadEvent(LEvent):
    """
    An event which is triggered when a file was uploaded
    """

    event_type: str = FILE_UPLOAD_EVENT_TYPE
    files: list[FileAttachment] = Field(default_factory=list)
    """The list of files which were uploaded"""
    upload_session_id: str = ""
    """Unique upload session ID"""


OnFileUploadCallback = Union[Callable, Callable[[LFileUploadEvent], None]]
"""Callback type definitions for callbacks of :attr:`LFileUpload.on_upload`"""


class LFileUpload(LWidget):
    """
    The LButton adds a button the log which upon click triggers it's
    click event.
    """

    def __init__(
        self,
        builder: "LogBuilder",
        name: str = "fileUpload",
        insert: bool = True,
        on_upload: OnFileUploadCallback | None = None,
        target: str | None = None,
    ):
        """
        :param builder: The log builder to which the button shall be added
        :param on_upload: Defines the function to be called when filed were uploaded
        :param name: The uploader's name
        :param insert: Defines if the element shall be inserted into the log
        :param target: Defines the cache entry in which new files shall be stored
        """
        super().__init__(name=name, builder=builder)
        if insert:
            self.insert_into_page()
        self._upload_session_total_files = 0
        """Total file count assumed in the current upload turn"""
        self._current_upload_session: str | None = None
        """Unique identifier of the current upload session"""
        self._current_files: dict[int, FileAttachment] = {}
        """The current list of files uploaded so far"""
        self.on_upload: OnFileUploadCallback | None = on_upload
        """Defines the function to be called when a file was uploaded"""
        self.target = target
        """Cache entry in which the file data shall be stored"""

    def write(self):
        html = self.render("{{TEMPLATES}}/extensions/upload/vl_file_upload.html")
        self.builder.html(html)

    def handle_event(self, event: "LEvent"):
        super().handle_event(event)
        if event.event_type == FILE_UPLOAD_EVENT_TYPE and event.widget == self:
            if self.on_upload:
                self.call_event_handler(self.on_upload, event)

    def handle_file_upload(self, request: WebRequest):
        """
        File upload handler which is called when a file is uploaded

        :param request: The upload request
        :return: The response
        """
        file_index = int(request.form.get("fileIndex", -1))
        file_count = int(request.form.get("fileCount", -1))
        session = request.form.get("uploadId", "")
        if file_index == -1 or file_count <= 0 or session == "":
            return
        if (
            self._current_upload_session is None
            or self._current_upload_session != session
        ):
            self._current_upload_session = session
            self._upload_session_total_files = file_count
        if file_index < 0 or file_index >= self._upload_session_total_files:
            return
        if file_index in self._current_files:
            return
        self._current_files[file_index] = request.files[0].freeze()
        if len(self._current_files) == self._upload_session_total_files:
            values: list[FileAttachment] = list(self._current_files.values())
            event_data = LFileUploadEvent(
                widget=self,
                files=values,
                upload_session_id=self._current_upload_session,
            )
            if self.target is not None:
                self.builder.cache.append(self.target, values, unpackap=True)
            self._current_upload_session = None
            self._current_files = {}
            self.raise_event(event_data)
