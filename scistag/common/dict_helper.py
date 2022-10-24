"""
Some helpful functions for working with dictionaries
"""

from __future__ import annotations


def dict_to_bullet_list(cd: dict | list,
                        level=0,
                        bold=False) -> str:
    """
    Converts a dictionary or a list to a nested bullet point list

    :param cd: The data element
    :param level: The nesting level depth
    :param bold: Defines if key names shall be printed bold
    :return: The assembled string
    """
    cur_str = ""
    bold_str = "**" if bold else ""
    tabs = "\t" * level
    if isinstance(cd, dict):
        for key, value in cd.items():
            if isinstance(value, dict) or isinstance(value, list):
                cur_str += tabs + f"* {bold_str}{key}{bold_str}:\n"
                cur_str += dict_to_bullet_list(value,
                                               level=level + 1,
                                               bold=bold)
            else:
                cur_str += tabs + f"* {bold_str}{key}{bold_str}: {value}\n"
    elif isinstance(cd, list):
        for element in cd:
            if isinstance(element, dict) or isinstance(element, list):
                cur_str += tabs + "*\n"
                cur_str += dict_to_bullet_list(element,
                                               level=level + 1,
                                               bold=bold)
            else:
                cur_str += tabs + "* " + element + "\n"
    return cur_str
