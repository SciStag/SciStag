"""
Provides functionality to easily add Emojis to the log
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union, Callable

from scistag.emojistag import EmojiDb, EmojiRenderer
from scistag.emojistag.emoji_info import EmojiInfo
from scistag.imagestag import Image
from scistag.vislog.extensions.builder_extension import BuilderExtension

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import LogBuilder


class EmojiLogger(BuilderExtension):
    """
    Helper class for logging adding emojis to the log
    """

    def __init__(self, builder: "LogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)
        self.show = self.__call__

    def find(self, search_mask: str = "") -> list[EmojiInfo]:
        """
        Search for an Emoji by search mask and returns it.

        For more advanced functions see scistag.emojistag.

        :param search_mask: The mask to search for, e.g. *monkey*
        :return: A list with all matching emojis found
        """
        results = EmojiDb.find_emojis_by_name(search_mask)
        return results

    def __call__(self, search_mask: str = "", size: int = None,
                 return_image: bool = False) -> Union["LogBuilder", Image]:
        """
        Logs an emoji to the log

        :param search_mask: The name for which we shall search in the emoji DB
        :param size: The desired output size. The standard text height by default.
        :param return_image: If defined the method will only return the first
            matching image found instead of inserting it into the log.

            If no valid image can be found the sad Emoji will be returned.
        :return: The LogBuilder if return_image is False, otherwise the image
        """
        if size is None:
            size = 14
        results = EmojiDb.find_emojis_by_name(search_mask)
        if len(results) == 0:
            results = EmojiDb.find_emojis_by_name("sad*")
        image = EmojiRenderer.render_emoji(results[0].name, size=size)
        if not return_image:
            self.builder.image.show(image, br=False)
            return self.builder
        return image
