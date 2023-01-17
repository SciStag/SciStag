from __future__ import annotations

from pydantic import BaseModel


class HtmlClientDebugOptions(BaseModel):
    """
    Html client debug options
    """

    log_updates: bool = False
    """Defines if modifications to the dom structure shall be logged"""
