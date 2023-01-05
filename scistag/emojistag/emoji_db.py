"""
Defines the class :class:`EmojiDb` which is the heart of this package.

It loads and provides information about all known Emojis and their details
such as the unicode encoding or their category.
"""

from __future__ import annotations
import io
import json
from fnmatch import fnmatch

import scistag.addons
from scistag.common.mt.stag_lock import StagLock
from scistag.common.essential_data import get_edp
from scistag.filestag.file_stag import FileStag

from .emoji_definitions import (
    EmojiIdentifierTypes,
    EMOJI_SVG_ADDON,
    EMOJI_NAMES,
    EMOJI_DB_NAME,
    EMOJI_NAMES_MARKDOWN,
)
from .emoji_info import EmojiInfo


class EmojiDb:
    """
    The Emoji DB provides Emoji and country flag graphics.
    By default it uses the Noto Emoji dataset embedded into the SciStag module.
    """

    _access_lock = StagLock()
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
    """
    The dictionary contains all official names of the emojis and their
    corresponding unicode sequence
    """
    _valid_sequences = set()
    "Set of valid unicode sequences"
    _main_dict = {}
    """
    Contains all details about every single known emoji such as name,
    category, subcategory and of course unicode sequence
    """

    @classmethod
    def _get_markdown_dict(cls) -> dict:
        """
        Returns the markdown name dictionary. Contains all common markdown
        emoji names as key and their corresponding unique sequence as value

        :return: The dictionary
        """
        with cls._access_lock:
            if len(cls._markdown_names) > 0:
                return cls._markdown_names
            edp = get_edp()
            file_data = FileStag.load(edp + EMOJI_NAMES_MARKDOWN)
            cls._markdown_names = json.load(io.BytesIO(file_data))
            return cls._markdown_names

    @classmethod
    def _get_unicode_dict(cls) -> dict:
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
            file_data = FileStag.load(edp + EMOJI_NAMES)
            cls._unicode_names = json.load(io.BytesIO(file_data))
            return cls._unicode_names

    @classmethod
    def get_all_valid_sequences(cls) -> set:
        """
        Returns a set of all (known) valid emoji sequences

        :return A set of valid emoji sequences (all uppercased and with
            an underscore separating the single elements)
        """
        with cls._access_lock:
            if len(cls._valid_sequences) > 0:
                return cls._valid_sequences
            unicode_dict = cls._get_unicode_dict()
            cls._valid_sequences = set(unicode_dict.values())
            return cls._valid_sequences

    @classmethod
    def _get_main_dict(cls) -> dict:
        """
        Returns the main dictionary containing all details about an emoji.

        :return: The dictionary
        """
        with cls._access_lock:
            if len(cls._main_dict) > 0:
                return cls._main_dict
            edp = get_edp()
            file_data = FileStag.load(edp + EMOJI_DB_NAME)
            cls._main_dict = json.load(io.BytesIO(file_data))
            # hotfix for property remaining, will be fixed with next data
            # update
            for key, value in cls._main_dict.items():
                value["sequence"] = key.split("_")
                value["category"] = value["group"]
                value["subcategory"] = value["subgroup"]
            return cls._main_dict

    @classmethod
    def get_sequence_for_name(cls, identifier: str) -> list:
        """
        Returns the unicode sequence for given unicode identifier

        :param identifier: Either the full qualified identifier as defined by
            unicode.org supporting all >3600 emojis as defined by unicode.org.
            or the markdown  shortcode enclosed by two colons such as ":deer:"
            as defined on GitHub.
        :return: The unicode sequence if the emoji could be found,
            otherwise an empty list
        """
        if identifier.startswith(":") and identifier.endswith(":"):
            return cls._get_markdown_dict().get(identifier[1:-1], "").split("_")
        unicode_dict = cls._get_unicode_dict()
        if identifier in unicode_dict:
            return cls._get_unicode_dict().get(identifier, "").split("_")
        sequence = identifier.encode("unicode-escape").decode("ascii")
        sequence = sequence.split("\\")[1:]
        sequence = [element.lstrip("Uu").lstrip("0") for element in sequence]
        if cls.validate_sequence(sequence):
            return sequence
        return []

    @classmethod
    def get_character_sequence(cls, identifier: EmojiIdentifierTypes) -> list[str]:
        """
        Converts an emoji identifier to a unicode character sequence which
        can be printed to the console or a markdown document.

        Does not alter the value if a unicode sequence was passed already.

        :param identifier: The emoji identifier, either it's unicode name,
            markdown name surrounded by colons or a single emoji character.
        :return: The unicode characters
        """
        if isinstance(identifier, str):
            identifier = cls.get_sequence_for_name(identifier)
        return identifier

    @classmethod
    def get_character(cls, identifier: EmojiIdentifierTypes) -> str:
        """
        :param identifier: The emoji's identifier

        :return: The emoji character (if valid), otherwise an empty string
        """
        sequence = cls.get_character_sequence(identifier)
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
        return "_".join(sequence).upper() in cls.get_all_valid_sequences()

    @classmethod
    def get_extensions(cls) -> dict:
        """
        Returns all available emoji extensions

        :return: Dictionary of extensions and their corresponding FileStag path
            to access their data
        """
        from scistag.imagestag import svg

        with cls._access_lock:
            if not cls._initialized:
                cls._extensions = scistag.addons.AddonManager.get_addons_paths(
                    "emojis.*"
                )
                cls._initialized = True
                cls._svg_emojis = (
                    EMOJI_SVG_ADDON in cls._extensions and svg.SvgRenderer.available()
                )
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
    def get_svg(cls, sequence: list[str]) -> bytes | None:
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
        emoji_path = (
            extensions[EMOJI_SVG_ADDON]
            + f"images/noto/emojis/svg/emoji_u{combined}.svg"
        )
        return FileStag.load(emoji_path)

    @classmethod
    def get_png(cls, sequence: list[str]) -> bytes | None:
        """
        Tries to read the SVG of an emoji from the database

        :param sequence: The unicode sequence, e.g. ["1f98c"] for a stag
        :return: The PNG data on success, otherwise None
        """
        lower_cased = [element.lower() for element in sequence]
        combined = "_".join(lower_cased)
        edp = get_edp()
        emoji_path = edp + f"images/noto/cpngs/emoji_u{combined}.png"
        return FileStag.load(emoji_path)

    @classmethod
    def png_exists(cls, sequence: list[str]) -> bool:
        """
        Returns if a PNG graphic for given emoji does exist in the local
        archive.

        :param sequence: The unicode sequence, e.g. ["1f98c"] for a stag
        :return: True if the PNG does exist.
        """
        lower_cased = [element.lower() for element in sequence]
        combined = "_".join(lower_cased)
        edp = get_edp()
        emoji_path = edp + f"images/noto/cpngs/emoji_u{combined}.png"
        return FileStag.exists(emoji_path)

    @classmethod
    def get_details(cls, sequence: list[str]) -> EmojiInfo | None:
        """
        Returns details about am emoji

        :param sequence: The unicode sequence without leading zeros.
        :return: The EmojiInfo object if available
        """
        main_db = cls._get_main_dict()
        upper_cased = [element.upper() for element in sequence]
        combined = "_".join(upper_cased)
        if combined in main_db:
            return EmojiInfo.parse_obj(main_db[combined])
        return None

    @classmethod
    def get_categories(cls) -> list[str]:
        """
        Returns a list of all emoji main categories

        :return: A list of all known emoji categories
        """
        main_dict = cls._get_main_dict()
        categories = set([element["category"] for element in main_dict.values()])
        return sorted(list(categories))

    @classmethod
    def get_sub_categories(cls, category: str) -> list[str]:
        """
        Returns a list of all emoji sub categories of given category

        :param category: The category's name
        :return: A list of subcategories in this category
        """
        main_dict = cls._get_main_dict()
        filtered_list = [
            element["subcategory"]
            for element in main_dict.values()
            if element["category"] == category
        ]
        return sorted(list(set(filtered_list)))

    @classmethod
    def get_emojis_in_category(
        cls, category: str, subcategory: str | None
    ) -> list[EmojiInfo]:
        """
        Returns all emojis in the defined category and subcategory

        :param category: The main category's name as obtained by
            :meth:`get_categories`.
        :param subcategory: The name of the subcategory. If no subcategory is
            provided all emojis in the category will be returned.
        :return: A list of all emojis in given category and subcategory
        """
        main_dict = cls._get_main_dict()
        if subcategory is not None:
            filtered_list = [
                EmojiInfo.parse_obj(element)
                for element in main_dict.values()
                if element["category"] == category
                and element["subcategory"] == subcategory
            ]
        else:
            filtered_list = [
                EmojiInfo.parse_obj(element)
                for element in main_dict.values()
                if element["category"] == category
            ]
        return sorted(filtered_list, key=lambda element: element.name)

    @classmethod
    def find_emojis_by_name(
        cls, name_mask: str, md: bool = False, find_all: bool = False
    ) -> list[EmojiInfo]:
        """
        Returns all emojis which match the defined search pattern

        :param name_mask: The name mask to search for, e.g *sun*
        :param md: Defines if the GitHub markdown db name shall be used instead
            of the full unicode name list.
        :param find_all: Defines if all emojis shall be returned, even when no
            graphic for them exists.
        :return: A list of all matching Emojis
        """
        main_dict = cls._get_main_dict()
        if md:
            result = [
                EmojiInfo.parse_obj(element)
                for element in main_dict.values()
                if fnmatch(element.get("markdownName", ""), name_mask)
            ]
        else:
            result = [
                EmojiInfo.parse_obj(element)
                for element in main_dict.values()
                if fnmatch(element["name"], name_mask)
            ]
        if not find_all:
            result = [element for element in result if cls.png_exists(element.sequence)]
        return result

    @classmethod
    def __getitem__(cls, key: str) -> EmojiInfo | None:
        """
        Returns the emoji details for a specific Emoji by it's name.

        :param key: Either the full qualified name as defined in the unicode
            database or its GitHub markdown name surrounded by colons, eg
            "deer" or ":deer:"
        :return: The Emoji description
        """
        sequence = cls.get_sequence_for_name(key)
        if len(sequence) > 0:
            return cls.get_details(sequence)
        raise KeyError("Emoji not found")


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
    return EmojiDb.get_character_sequence(identifier=identifier)


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
    return EmojiDb.get_details(EmojiDb.get_character_sequence(identifier))


def find_emojis_by_name(name_mask: str, md: bool = False):
    """
    Returns all emojis which match the defined search pattern

    :param name_mask: The name mask to search for, e.g *sun*
    :param md: Defines if the GitHub markdown db name shall be used instead
        of the full unicode name list.
    :return: A list of all matching Emojis
    """
    return EmojiDb.find_emojis_by_name(name_mask=name_mask, md=md)
