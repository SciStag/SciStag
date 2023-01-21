"""
Defines the class :class:`CacheOptions` which configures the cache.
"""

from __future__ import annotations

from typing import Union

from pydantic import BaseModel


class CacheOptions(BaseModel):
    """
    Defines the cache configuration
    """

    version: int = 1
    """The cache version. 1 by default.

    When ever you change this version all old cache values will be
    removed and/or ignored from the cache."""
    dir: Union[str, None] = None
    """The directory in which data which shall be cached
    between multiple execution sessions shall be dumped to disk.    
    By default "{target_dir}/.stscache"."""
    name: str = ""
    """The cache's identifier. If multiple logs store data
    into the same logging directory this can be used to ensure their
    caching directories don't accidentally overlap w/o having to
    provide the whole path via cache_dir."""

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
