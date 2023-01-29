"""
Defines the class :class:`PageDescription` which describes a single sub page of a
dynamic VisualLog application.
"""

from typing import Union


class PageDescription:
    """
    Describes a single, embedded page of a VisualLog
    """

    name: str
    """The page's name"""
    default_tab: Union[str, None] = None
    """The tab to be selected when this page is entered"""
