"""
Implements the :class:`NumpyLogger` extension for LogBuilder to log
numpy data such as matrices and vectors.
"""
from __future__ import annotations

from scistag.common.trees.text_tree import (
    TextTreeNode,
    TextTreeBuilderOptions,
    TextTree,
)
from scistag.vislog import BuilderExtension, LogBuilder


class CollectionLogger(BuilderExtension):
    """
    The collection logger as the possibility to add collections to the log
    such as standard :class:`list`s or :class:`dict`s.
    """

    def __init__(self, builder: LogBuilder):
        """
        :param builder: The builder we are using to write to the log
        """
        super().__init__(builder)
        self.add = self.__call__

    def __call__(self, data: dict | list):
        """
        Logs a dictionary or a list.

        The data needs to be JSON compatible so can contain further nested
        diotionaries, lists, floats, booleans or integers but no more
        complex types.

        :param data: The dictionary or list
        """
        options = TextTreeBuilderOptions()
        options.identifier_prefix = "**"
        options.identifier_postfix = ": **"
        dict_tree = str(TextTree.from_collection(data, options=options))
        self.builder.md(dict_tree, exclude_targets={"txt"})
        if self.builder.page_session.txt_export:
            dict_tree_txt = str(TextTree.from_collection(data))
            self.builder.add_txt(dict_tree_txt)
