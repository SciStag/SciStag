"""
Implements the WebRequest class which is a wrapper around a classic Flask
request object.
"""

from __future__ import annotations
from typing import Union
from dataclasses import dataclass


@dataclass
class WebRequest:
    """
    Defines the parameters of a web request
    """
    path: str
    "The absolute url path (excluding host/IP)"
    relative_path: str
    "The relative URL path"
    method: str
    "The request method, e.g. GET, POST, PUT etc."
    headers: dict
    "The headers passed in"
    body: Union[bytes, None]
    "The body data of the POST request"
    parameters: dict
    "The query parameters"
    base_url: str
    "The base url, e.g. http://localhost/myClass/myMethod"
    url: str
    "The full url pointing to our service http://localhost/myClass/myMethod"
    host_url: str
    "The url to the host, e.g. http://localhost"
    remote_addr: str
    "The clients' IP, e.g. 192.168.3.98"
    environ: dict
    "The request headers, e.g. \"HTTP_USER_AGENT\""
    url_root: str
    "The url of the blueprint/service being called, e.g.  http://localhost/"
    mimetype: str
    "The request body's content type, e.g. image/jpeg"
    host: str
    "The host name/IP, e.g. localhost"
