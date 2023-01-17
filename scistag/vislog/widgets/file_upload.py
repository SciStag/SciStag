"""
Implements the class :class:`LFileUpload` which allows the user to upload files to
the server.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Union

from scistag.vislog.widgets.log_widget import LWidget
from scistag.vislog.widgets.event import LEvent
from scistag.webstag.server import WebRequest, FileAttachment

DEFAULT_MAX_FILE_COUNT = 20
"The default maximum file count"

DEFAULT_MAX_GALLERY_PREVIEW_SIZE = 5000000
"The default maximum of size shown in the preview gallery"

DEFAULT_MAX_UPLOAD_SIZE = 10 * 1024 * 1024
"The default maximum upload size (10 MB)"

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
    files: list[FileAttachment] = field(default_factory=list)
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
        types: str = "file/*",
        max_file_count: int = 1,
        on_upload: OnFileUploadCallback | None = None,
        name: str = "fileUpload",
        insert: bool = True,
        upload_text: str | None = None,
        button_text: str | None = None,
        target: str | None = None,
        max_upload_size: int | None = None,
        gallery_items: int = 0,
        max_gallery_preview_size: int | None = None,
    ):
        """
        :param builder: The log builder to which the button shall be added
        :param types: Defines the types of images supported. Either mime type
            or a list of file extensions, separated by comma.

            See :module:`scistag.web_stag.mime_types` for a set of example mime types
            such as MIME_TYPE_FILE_ALL, MIME_TYPE_IMAGE_ALL.
        :param max_file_count: The maximum number of files which can be uploaded at once
        :param max_upload_size: The maximum size of a file which can be uploaded
        :param on_upload: Defines the function to be called when filed were uploaded
        :param name: The uploader's name
        :param insert: Defines if the element shall be inserted into the log
        :param upload_text: The text to show at the top of the upload
            box.
        :param button_text: The text to show in the button caption
        :param target: Defines the cache entry in which new files shall be stored
        :param gallery_items: The maximum count of images to preview in the
            upload area.
        :param max_gallery_preview_size: The maximum size of images to show in the
            preview area.
        """
        super().__init__(name=name, builder=builder)
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
        multiple = max_file_count > 1
        """Defines if multiple files can be uploaded in one go"""
        file_ph = f"files" if multiple else "file"
        if types.startswith("image/") and ";" not in types:
            file_ph = f"images" if multiple else "image"
        if types.startswith("video/") and ";" not in types:
            file_ph = f"videos" if multiple else "video"
        if upload_text is None:
            upload_text = (
                f"Please drop the {file_ph} <b>here</b> you would like to " f"upload"
            )
        else:
            upload_text = self.builder.encode_html(upload_text)
        self.upload_text = upload_text
        if button_text is None:
            button_text = f"Select {file_ph}"
        else:
            button_text = self.builder.encode_html(button_text)
        """Text to be displayed in the upload box"""
        self.button_text = button_text
        """Defines the text to show in the upload button"""
        self.accepted_types = types
        """Accepted mime types supported"""
        self.max_gallery_items = gallery_items
        if max_gallery_preview_size is None:
            max_gallery_preview_size = DEFAULT_MAX_GALLERY_PREVIEW_SIZE
        self.gallery_max_preview_size = max_gallery_preview_size
        if max_upload_size is None:
            max_upload_size = DEFAULT_MAX_UPLOAD_SIZE
        self.max_upload_size = max_upload_size
        self.max_file_count = max_file_count

        if insert:
            self.insert_into_page()

    def write(self):
        max_gallery_items = self.max_gallery_items
        show_gallery = "1" if max_gallery_items > 0 else "0"
        replacements = {
            "UPLOAD INFO HERE": self.upload_text,
            "image/*": self.accepted_types,
            "Select files": self.button_text,
            'data-show_gallery="1"': f'data-show_gallery="{show_gallery}"',
            'data-max_file_count="20"': f'data-max_file_count="{self.max_file_count}"',
            'data-gallery_items="9"': f'data-gallery_items="{max_gallery_items}"',
            'data-max_preview_size="500000"': f'data-max_preview_size="{self.gallery_max_preview_size}"',
            'data-max_upload_size="1500000"': f'data-max_upload_size="{self.max_upload_size}"',
        }
        if self.max_file_count == 1:
            replacements[" multiple"] = ""
        html = self.render(
            "{{TEMPLATES}}/extensions/upload/vl_file_upload.html",
            replacements=replacements,
        )
        self.page_session.write_html(html)
        self.builder.add_txt("<<FILE UPLOAD WIDGET>>", targets="*")

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
                self.builder.cache.lpush(self.target, values, unpack=True)
            self._current_upload_session = None
            self._current_files = {}
            self.raise_event(event_data)
