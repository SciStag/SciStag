from pydantic import BaseModel

from scistag.emojistag import (EmojiDb, get_emoji_character,
                               get_emoji_details, get_emoji_sequence,
                               get_emoji_sequence_valid, find_emojis_by_name)


def test_get_emoji_svg():
    """
    Tests if an SVG emoji can be loaded from the EmojiDB
    """
    svg_data = EmojiDb.get_svg(["1f3c3"])
    assert svg_data is not None
    assert len(svg_data) == 13716


def test_get_markdown_dict():
    """
    Tests if the markdown dictionary is valid
    """
    md_dict = EmojiDb._get_markdown_dict()
    assert len(md_dict) > 0
    deer_emoji = EmojiDb.get_sequence_for_name(":deer:")
    assert deer_emoji == ["1F98C"]
    assert deer_emoji == EmojiDb._get_unicode_dict()["deer"].split("_")


def test_unicode_dict():
    """
    Tests if the unicode dictionary is valid
    """
    unicode_dict = EmojiDb._get_unicode_dict()
    assert len(unicode_dict) > 3600
    assert EmojiDb.get_sequence_for_name("deer") == ["1F98C"]
    assert EmojiDb.get_sequence_for_name("flag: Germany") == ['1F1E9',
                                                              '1F1EA']


def test_emoji_db():
    """
    Tests the main DB
    """
    sequence = EmojiDb.get_character_sequence("🦌")
    assert sequence == ["1f98c"]
    character = EmojiDb.get_character(sequence)
    assert character == "🦌"
    details = EmojiDb.get_details(["1F98C"])
    assert details is not None
    assert details.name == "deer"
    assert details.category == "Animals & Nature"
    assert details.subcategory == "animal-mammal"
    assert details.markdownName == "deer"


def test_conversion():
    """
    Tests conversion from different representations
    """
    sequence = EmojiDb.get_character_sequence("🦌")
    character = EmojiDb.get_character(sequence)
    details = EmojiDb.get_details(["1F98C"])
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


def test_search():
    """
    Tests the search for single categories and emojis by name
    """
    categories = EmojiDb.get_categories()
    assert categories == ['Activities',
                          'Animals & Nature',
                          'Component',
                          'Flags',
                          'Food & Drink',
                          'Objects',
                          'People & Body',
                          'Smileys & Emotion',
                          'Symbols',
                          'Travel & Places']
    sub_categories = EmojiDb.get_sub_categories("Animals & Nature")
    assert sub_categories == ['animal-amphibian',
                              'animal-bird',
                              'animal-bug',
                              'animal-mammal',
                              'animal-marine',
                              'animal-reptile',
                              'plant-flower',
                              'plant-other']
    mammals = EmojiDb.get_emojis_in_category("Animals & Nature",
                                             "animal-mammal")
    assert len(mammals) == 66
    assert "deer" in [cur.name for cur in mammals]

    # search by name
    results = EmojiDb.find_emojis_by_name("*sunglasses*")
    assert len(results) == 3

    # search by name in markdown
    results = EmojiDb.find_emojis_by_name("*sunglasses*", md=True)
    assert len(results) == 2

    assert results == find_emojis_by_name("*sunglasses*", md=True)

    # verify retrieval via item selection
    sun_glasses = EmojiDb()[":dark_sunglasses:"]
    assert sun_glasses.name == "sunglasses"

    # verify standard image
    image = sun_glasses.image
    assert image.width == 136 and image.height == 128
