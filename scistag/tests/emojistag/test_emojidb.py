from pydantic import BaseModel

from scistag.emojistag import (EmojiDb, get_emoji_character,
                               get_emoji_details, get_emoji_sequence,
                               get_emoji_sequence_valid)


def test_get_emoji_svg():
    """
    Tests if an SVG emoji can be loaded from the EmojiDB
    """
    svg_data = EmojiDb.get_emoji_svg(["1f3c3"])
    assert svg_data is not None
    assert len(svg_data) == 13716


def test_get_markdown_dict():
    """
    Tests if the markdown dictionary is valid
    """
    md_dict = EmojiDb.get_markdown_dict()
    assert len(md_dict) > 0
    deer_emoji = EmojiDb.get_emoji_sequence_for_name(":deer:")
    assert deer_emoji == ["1F98C"]
    assert deer_emoji == EmojiDb.get_unicode_dict()["deer"].split("_")


def test_unicode_dict():
    """
    Tests if the unicode dictionary is valid
    """
    unicode_dict = EmojiDb.get_unicode_dict()
    assert len(unicode_dict) > 3600
    assert EmojiDb.get_emoji_sequence_for_name("deer") == ["1F98C"]
    assert EmojiDb.get_emoji_sequence_for_name("flag: Germany") == ['1F1E9',
                                                                    '1F1EA']


def test_emoji_db():
    """
    Tests the main DB
    """
    sequence = EmojiDb.get_sequence("🦌")
    assert sequence == ["1f98c"]
    character = EmojiDb.get_character(sequence)
    assert character == "🦌"
    details = EmojiDb.get_emoji_details(["1F98C"])
    assert details is not None
    assert details.name == "deer"
    assert details.group == "Animals & Nature"
    assert details.subgroup == "animal-mammal"
    assert details.markdownName == "deer"


def test_conversion():
    """
    Tests conversion from different representations
    """
    sequence = EmojiDb.get_sequence("🦌")
    character = EmojiDb.get_character(sequence)
    details = EmojiDb.get_emoji_details(["1F98C"])
    assert get_emoji_character(sequence) == character
    assert get_emoji_details(character) == details
    character = "🇩🇪"
    flag_details = get_emoji_details(character)
    assert flag_details.countryCode == "DE"
    assert flag_details.countryName == "Germany"
    assert flag_details.markdownName == "de"
    medium_woman = "👩🏽"
    combiner_details = get_emoji_details(medium_woman)
    assert combiner_details.name == "woman: medium skin tone"
    assert not get_emoji_sequence_valid(get_emoji_sequence("NonSense"))
    assert get_emoji_sequence_valid(get_emoji_sequence(medium_woman))
