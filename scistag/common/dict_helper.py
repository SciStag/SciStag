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
                cur_str += f"{tabs}* {bold_str}{key}{bold_str}:\n"
                cur_str += dict_to_bullet_list(value,
                                               level=level + 1,
                                               bold=bold)
            else:
                cur_str += f"{tabs}* {bold_str}{key}{bold_str}: {value}\n"
    elif isinstance(cd, list):
        flat = False
        if len(cd) <= 4:
            flat = True
            for element in cd:
                if element is not None and not isinstance(element,
                                                          (float, bool, int)):
                    flat = False
                    break
        if flat:
            elements = ", ".join([str(element) for element in cd])
            cur_str += f"{tabs} {elements}"
            return cur_str
        for element in cd:
            if isinstance(element, dict) or isinstance(element, list):
                if isinstance(element, dict):
                    cur_str += f"{tabs}* {{\n"
                else:
                    cur_str += f"{tabs}* [\n"
                cur_str += dict_to_bullet_list(element,
                                               level=level + 1,
                                               bold=bold)
                if isinstance(element, dict):
                    cur_str += f"\n{tabs}* }}\n"
                else:
                    cur_str += f"{tabs} ]\n"
            else:
                cur_str += f"{tabs}* " + str(element) + "\n"
    return cur_str
