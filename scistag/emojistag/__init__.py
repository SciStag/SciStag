"""
EmojiStag provides Emoji graphics - pre-rendered or live-rendered using
vector files - and methods to get detailed information about emojis or
to convert markdown short-codes to unicode sequences and vice versa.
"""

from .emoji_db import (
    EmojiDb,
    get_emoji_sequence,
    get_emoji_details,
    get_emoji_character,
    EmojiIdentifierTypes,
    get_emoji_sequence_valid,
    find_emojis_by_name,
)
from .emoji_renderer import EmojiRenderer, render_emoji

__all__ = [
    "EmojiRenderer",
    "EmojiDb",
    "get_emoji_sequence",
    "render_emoji",
    "get_emoji_character",
    "get_emoji_details",
    "find_emojis_by_name",
    "get_emoji_sequence_valid",
    "EmojiIdentifierTypes",
]
