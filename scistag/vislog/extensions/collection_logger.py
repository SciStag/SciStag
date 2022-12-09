"""
Implements the :class:`NumpyLogger` extension for VisualLogBuilder to log
numpy data such as matrices and vectors.
"""
from __future__ import annotations

from scistag.vislog import BuilderExtension, VisualLogBuilder


class CollectionLogger(BuilderExtension):
    """
    The collection logger as the possibility to add collections to the log
    such as standard :class:`list`s or :class:`dict`s.
    """

    def __init__(self, builder: VisualLogBuilder):
        """
        :param builder: The builder we are using to write to the log
        """
        super().__init__(builder)
        self.log = self.__call__

    @classmethod
    def dict_to_bullet_list(cls,
                            cd: dict | list,
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
                    cur_str += cls.dict_to_bullet_list(value,
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
                                                              (float, bool,
                                                               int)):
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
                    cur_str += cls.dict_to_bullet_list(element,
                                                       level=level + 1,
                                                       bold=bold)
                    if isinstance(element, dict):
                        cur_str += f"\n{tabs}* }}\n"
                    else:
                        cur_str += f"{tabs} ]\n"
                else:
                    cur_str += f"{tabs}* " + str(element) + "\n"
        return cur_str

    def __call__(self, data: dict | list):
        """
        Logs a dictionary or a list.

        The data needs to be JSON compatible so can contain further nested
        diotionaries, lists, floats, booleans or integers but no more
        complex types.

        :param data: The dictionary or list
        """
        dict_tree = self.dict_to_bullet_list(data, level=0, bold=True)
        self.builder.md(dict_tree, exclude_targets={'txt'})
        if self.target_log.txt_export:
            dict_tree_txt = self.dict_to_bullet_list(data, level=0,
                                                     bold=False)
            self.builder.add_txt(dict_tree_txt)
