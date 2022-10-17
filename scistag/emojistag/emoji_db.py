from __future__ import annotations
import io
import json
from threading import RLock
from typing import Union, Optional

from pydantic import BaseModel

import scistag.addons
from scistag.common.essential_data import get_edp
from scistag.filestag import FileStag
from scistag.imagestag import svg

EmojiIdentifierTypes = Union[str, list[str]]
"""
An emoji name such as "deer" (see :meth:`EmojiDb.get_unicode_dict`, a  markdown
emoji identifier such as ``":deer:"`` (GitHub definitions), a single unicode
character or a unicode sequence (without leading zeros).
"""

EMOJI_SVG_ADDON = "emojis.svg"
"Addon name for SVG emojis"

_EMOJI_DB_NAME = "data/emoji/emoji_db.json"
"Main emoji database file, containing detailed information about all Emojis"
_EMOJI_NAMES = "data/emoji/emoji_names.json"
"""
Emoji conversion dictionary. Containing the unicode codes for all unicode codes 
as defined by unicode.org
"""
_EMOJI_NAMES_MARKDOWN = "data/emoji/markdown_emoji_names.json"
"""
Markdown emoji conversion dictionary. Containing the unicode codes for common 
Emoji names used in markdown
"""


class EmojiInfo(BaseModel):
    """
    Contains the information about a single emoji
    """
    name: str
    "The emojis name as defined in the unicode standard, e.g. Older Woman"
    group: str
    "The emoji's group, e.g. Animals & Nature"
    subgroup: str
    "The emoji's sub group, e.g. animal-mammal"
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


class EmojiDb:
    """
    The Emoji DB provides Emoji and country flag graphics.
    By default it uses the Noto Emoji dataset embedded into the SciStag module.
    """

    _access_lock = RLock()
    "Shared access lock"
    _initialized = False
    "Defines if the emoji db was initialized"
    _extensions = {}
    "List of known emoji addon packages"
    _svg_emojis = False
    "Defines if SVG emojis are available"
    _markdown_names = {}
    "Markdown name conversion dictionary"
    _unicode_names = {}
    "Unicode name conversion dictionary"
    _valid_sequences = set()
    "Set of valid unicode sequences"
    _main_dict = {}
    "Unicode name conversion dictionary"

    @classmethod
    def get_markdown_dict(cls) -> dict:
        """
        Returns the markdown name dictionary. Contains all common markdown
        emoji names as key and their corresponding unique sequence as value

        :return: The dictionary
        """
        with cls._access_lock:
            if len(cls._markdown_names) > 0:
                return cls._markdown_names
            edp = get_edp()
            file_data = FileStag.load_file(edp + _EMOJI_NAMES_MARKDOWN)
            cls._markdown_names = json.load(io.BytesIO(file_data))
            return cls._markdown_names

    @classmethod
    def get_unicode_dict(cls) -> dict:
        """
        Returns the unicode name dictionary. Contains all common emoji names as
        key and their corresponding unique sequence as value for more than
        3600 emojis. See unicode.org for more details.

        :return: The dictionary
        """
        with cls._access_lock:
            if len(cls._unicode_names) > 0:
                return cls._unicode_names
            edp = get_edp()
            file_data = FileStag.load_file(edp + _EMOJI_NAMES)
            cls._unicode_names = json.load(io.BytesIO(file_data))
            return cls._unicode_names

    @classmethod
    def get_valid_sequences(cls) -> set:
        """
        Returns a set of valid emoji sequences

        :return A set of valid emoji sequences (all uppercased)
        """
        with cls._access_lock:
            if len(cls._valid_sequences) > 0:
                return cls._valid_sequences
            unicode_dict = cls.get_unicode_dict()
            cls._valid_sequences = set(unicode_dict.values())
            return cls._valid_sequences

    @classmethod
    def get_main_dict(cls) -> dict:
        """
        Returns the main dictionary containing all details about an emoji.

        :return: The dictionary
        """
        with cls._access_lock:
            if len(cls._main_dict) > 0:
                return cls._main_dict
            edp = get_edp()
            file_data = FileStag.load_file(edp + _EMOJI_DB_NAME)
            cls._main_dict = json.load(io.BytesIO(file_data))
            return cls._main_dict

    @classmethod
    def get_emoji_sequence_for_name(cls, identifier: str) -> list:
        """
        Returns the unicode sequence for given unicode identifier

        :param identifier: Either the full qualified identifier as defined by
            unicode.org supporting all >3600 emojis, see
            :meth:`get_unicode_dict()` for the full list or the markdown
            shortcode enclosed by two colons such as ":deer:"
            as defined in :meth:`get_markdown_dict()`.
        :return: The unicode sequence if the emoji could be found,
            otherwise an empty list
        """
        if identifier.startswith(":") and identifier.endswith(":"):
            return cls.get_markdown_dict().get(identifier[1:-1], "").split("_")
        unicode_dict = cls.get_unicode_dict()
        if identifier in unicode_dict:
            return cls.get_unicode_dict().get(identifier, "").split("_")
        sequence = identifier.encode('unicode-escape').decode('ascii')
        sequence = sequence.split("\\")[1:]
        sequence = [element.lstrip("Uu").lstrip("0") for element in sequence]
        if cls.validate_sequence(sequence):
            return sequence
        return []

    @classmethod
    def get_sequence(cls, identifier: EmojiIdentifierTypes) -> list[str]:
        """
        Converts an emoji identifier to a  unicode sequence. Does not alter
        the value if a unicode sequence was passed already.

        :param identifier: The emoji identifier, either it's unicode name,
            markdown name surrounded by colons or a single emoji character.
        :return: The unicode sequence
        """
        if isinstance(identifier, str):
            identifier = cls.get_emoji_sequence_for_name(identifier)
        return identifier

    @classmethod
    def get_character(cls, identifier: EmojiIdentifierTypes) -> str:
        """
        :param identifier: The emoji's identifier

        :return: The emoji character (if valid), otherwise an empty string
        """
        sequence = cls.get_sequence(identifier)
        if len(sequence) == 0:
            return ""
        encoding = "".join(["\\U" + element.zfill(8) for element in sequence])
        ascii_encoding = encoding.encode("ASCII")
        return ascii_encoding.decode("unicode-escape")

    @classmethod
    def validate_sequence(cls, sequence: list[str]):
        """
        Returns if given sequence is known (in the current version) of our
        Emoji database.

        :param sequence: The sequence as unicode characters without leading
            zeros.
        :return: True if the sequence is known
        """
        return "_".join(sequence).upper() in cls.get_valid_sequences()

    @classmethod
    def get_extensions(cls) -> dict:
        """
        Returns all available emoji extensions

        :return: Dictionary of extensions and their corresponding FileStag path
            to access their data
        """
        with cls._access_lock:
            if not cls._initialized:
                cls._extensions = \
                    scistag.addons.AddonManager.get_addons_paths("emojis.*")
                cls._initialized = True
                cls._svg_emojis = \
                    EMOJI_SVG_ADDON in cls._extensions and \
                    svg.SvgRenderer.available()
        return cls._extensions

    @classmethod
    def get_svg_support(cls) -> bool:
        """
        Returns if SVG rendering is supported tne SVG repo installed

        :return: True if high quality rendering is possible
        """
        cls.get_extensions()
        return cls._svg_emojis

    @classmethod
    def get_emoji_svg(cls, sequence: list[str]) -> bytes | None:
        """
        Tries to read the SVG of an emoji from the database

        :param sequence: The unicode sequence, e.g. ["u1f98c"] for a stag
        :return: The SVG data on success, otherwise None
        """
        extensions = cls.get_extensions()
        if EMOJI_SVG_ADDON not in extensions:
            return None
        lower_cased = [element.lower() for element in sequence]
        combined = "_".join(lower_cased)
        emoji_path = \
            extensions[
                EMOJI_SVG_ADDON] + \
            f"images/noto/emojis/svg/emoji_u{combined}.svg"
        return FileStag.load_file(emoji_path)

    @classmethod
    def get_emoji_png(cls,
                      sequence: list[str]) -> bytes | None:
        """
        Tries to read the SVG of an emoji from the database

        :param sequence: The unicode sequence, e.g. ["1f98c"] for a stag
        :return: The SVG data on success, otherwise None
        """
        lower_cased = [element.lower() for element in sequence]
        combined = "_".join(lower_cased)
        edp = get_edp()
        emoji_path = edp + f"images/noto/cpngs/emoji_u{combined}.png"
        return FileStag.load_file(emoji_path)

    @classmethod
    def get_emoji_details(cls, sequence: list[str]) -> EmojiInfo | None:
        """
        Returns details about am emoji

        :param sequence: The unicode sequence without leading zeros.
        :return: The EmojiInfo object if available
        """
        main_db = cls.get_main_dict()
        upper_cased = [element.upper() for element in sequence]
        combined = "_".join(upper_cased)
        if combined in main_db:
            return EmojiInfo.parse_obj(main_db[combined])
        return None


def get_emoji_sequence(identifier: EmojiIdentifierTypes) -> list[str]:
    """
    Converts an emoji name such as ``"deer"``,
    (see :meth:`EmojiDb.get_unicode_dict`, a markdown
    emoji identifier such as ``":deer:"`` (see GitHub) or a single unicode
    character to a unicode sequence.

    Does not alter the value if a unicode sequence was passed already.

    :param identifier: The emoji identifier, either it's name such as "deer",
        it's markdown name such as ":deer:" or a single unicode character
        like 🦌 a unicode sequence as list of strings.
    :return: The unicode sequence, e.g. ["1f98c"] for a deer
    """
    return EmojiDb.get_sequence(identifier=identifier)


def get_emoji_sequence_valid(sequence: list[str]) -> bool:
    """
    Returns if given emoji sequence is know to our current database

    :param sequence: The sequence, a lift of unicode sequence components
        without leading zeros as returned by :meth:`get_emoji_sequence`.
    :return: True if the sequence is known
    """
    return EmojiDb.validate_sequence(sequence)


def get_emoji_character(identifier: EmojiIdentifierTypes) -> str:
    """
    Returns the emoji unicode character for an emoji name.

    :param identifier: The emoji identifier, either it's name such as "deer",
        it's markdown name such as ":deer:" or a single unicode character
        like 🦌 or a unicode sequence as list of strings.
    :return: If the Emoji could be found a single unicode emoji character
        such as 🦌, otherwise an empty string.
    """
    return EmojiDb.get_character(identifier)


def get_emoji_details(identifier: EmojiIdentifierTypes) -> EmojiInfo | None:
    """
    Returns details about am emoji

    :param identifier: The emoji identifier, either it's name such as "deer",
        it's markdown name such as ":deer:", a single unicode character
        like 🦌 or a combined character like 🇩🇪.
    :return: The Emoji info object if available providing all information
        about the emoji stored in our db.
    """
    sequence = EmojiDb.get_sequence(identifier)
    return EmojiDb.get_emoji_details(sequence)
