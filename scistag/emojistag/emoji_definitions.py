from typing import Union

EmojiIdentifierTypes = Union[str, list[str]]
"""
An emoji name such as "deer" (see :meth:`EmojiDb.get_unicode_dict`, a  markdown
emoji identifier such as ``":deer:"`` (GitHub definitions), a single unicode
character or a unicode sequence (without leading zeros).
"""

EMOJI_SVG_ADDON = "emojis.svg"
"Addon name for SVG emojis"

EMOJI_DB_NAME = "data/emoji/emoji_db.json"
"Main emoji database file, containing detailed information about all Emojis"
EMOJI_NAMES = "data/emoji/emoji_names.json"
"""
Emoji conversion dictionary. Containing the unicode codes for all unicode codes 
as defined by unicode.org
"""
EMOJI_NAMES_MARKDOWN = "data/emoji/markdown_emoji_names.json"
"""
Markdown emoji conversion dictionary. Containing the unicode codes for common 
Emoji names used in markdown
"""
