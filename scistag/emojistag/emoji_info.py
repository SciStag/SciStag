"""
Defines the class :class:`EmojiInfo` which defines all details about an emoji
and an image property to retrieve its image in the default size.
"""

from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from scistag.imagestag.image import Image


class EmojiInfo(BaseModel):
    """
    Contains the information about a single emoji
    """
    sequence: list[str]
    "The unique identification sequence"
    name: str
    "The emojis name as defined in the unicode standard, e.g. Older Woman"
    category: str
    "The emoji's category, e.g. Animals & Nature"
    subcategory: str
    "The emoji's subcategory, e.g. animal-mammal"
    markdownName: Optional[str]
    """
    If there is a GitHub markdown shortcut for the emoji it's provided here.

    Note that that EmojiStag and SciStag might not used the same definition
    version at all times but all common emojis should be available.
    """
    countryCode: Optional[str]
    """
    If the emoji is a country flag it's two letter code, e.g. DE for Germany
    is provided here
    """
    countryName: Optional[str]
    """
    The full country name in English such as Germany
    """

    @property
    def image(self) -> "Image":
        """
        The image in its default resolution of 13x128 pixels.

        For more advanced versions see :func:`render_emoji`
        """
        from .emoji_renderer import render_emoji
        return render_emoji(self.sequence)
