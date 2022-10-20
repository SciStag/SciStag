"""
Implements the class :class:`WebResponse` which is returned from services
added to a :class:`WebStagService`.
"""

from __future__ import annotations
from typing import Union
from dataclasses import dataclass


@dataclass
class WebResponse:
    body: Union[bytes, str, None]
    "The response body. Either, text, binary raw data or nothing"
    status: int = 200
    "The response code (e.g 200 = OK)"
    cache: bool = False
    "Defines if the response may be cached"
