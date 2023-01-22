"""
WebStag.Server Provides a wrapper for even more easily hosting WebServices
via Flask or FastAPI
"""

from .web_request import WebRequest, FileAttachment
from .web_response import WebResponse
from .web_stag_service import WebStagService
from .web_stag_server import WebStagServer
from .class_service import WebClassService
from .class_service_entry import WebClassServiceEntry

__all__ = [
    "WebRequest",
    "WebResponse",
    "FileAttachment",
    "WebStagService",
    "WebStagServer",
    "WebClassService",
    "WebClassServiceEntry",
]
