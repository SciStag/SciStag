"""
Implements the WebRequest class which is a wrapper around a classic Flask
request object.
"""

from __future__ import annotations
from typing import Union
from dataclasses import dataclass, field


@dataclass
class FileAttachment:
    """
    Defines a file attachment attached to a :class:`WebRequest`
    """

    filename: str | None = None
    """Defines the element's filename (if known)"""
    data: bytes | None = None
    """Defines the element's data. In case of an error this can be None"""
    mimetype: str | None = None
    """Defines the element's mimetype - if provided"""

    def freeze(self) -> FileAttachment:
        """
        Receives all content from the client and freezes the data.

        If you intend to collect file attachments received from a client and user it
        at some later point in time you need to call this method to ensure all data was
        transferred. It will convert a dynamic data stream to an in-memory storage
        of the file data if required.

        :return: Self
        """
        return self

    def save_to(self, target: str) -> bool:
        """
        Saves the attachment to the file path defined

        :param target: The target name
        :return: True on success
        """
        from scistag.filestag import FileStag

        return FileStag.save(target, data=self.data)


@dataclass
class WebRequest:
    """
    Defines the parameters of a web request
    """

    path: str = ""
    "The absolute url path (excluding host/IP)"
    relative_path: str = ""
    "The relative URL path"
    method: str = ""
    "The request method, e.g. GET, POST, PUT etc."
    headers: dict = field(default_factory=dict)
    "The headers passed in"
    form: dict = field(default_factory=dict)
    "The requests form data"
    files: list[FileAttachment] = field(default_factory=list)
    "List of attached files"
    body: Union[bytes, None] = None
    "The body data of the POST request"
    parameters: dict = field(default_factory=dict)
    "The query parameters"
    base_url: str = ""
    "The base url, e.g. http://localhost/myClass/myMethod"
    url: str = ""
    "The full url pointing to our service http://localhost/myClass/myMethod"
    host_url: str = ""
    "The url to the host, e.g. http://localhost"
    remote_addr: str = ""
    "The clients' IP, e.g. 192.168.3.98"
    environ: dict = field(default_factory=dict)
    'The request headers, e.g. "HTTP_USER_AGENT"'
    url_root: str = ""
    "The url of the blueprint/service being called, e.g.  http://localhost/"
    mimetype: str = ""
    "The request body's content type, e.g. image/jpeg"
    host: str = ""
    "The host name/IP, e.g. localhost"
