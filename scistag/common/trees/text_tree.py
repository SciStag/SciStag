"""
Implements the classes :class:`TextTreeNode` and :class:`TextTree` which
allow the conversion of collection types such as dictionaries and lists to
a tree of text which can then be printed to a document or a debug output.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Callable

from .tree_node import TreeNode, TreeConfig


class TextTreeNode(TreeNode):
    """
    Defines a single node of a tree which leafs contain text data, for example
    to build a list of bullet points in a text document.
    """

    def __init__(self, text: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        "The text which shall be displayed in the output tree"

    @classmethod
    def _branch_to_text(cls, node: TextTreeNode, tabs: str):
        """
        Converts the current branch to a bullet list text

        :param node: The current node
        :param tabs: The current tab depth
        :return: The result string
        """
        target = tabs + "* " + str(node) + "\n"
        for child in node.children:
            child: TextTreeNode
            target += cls._branch_to_text(child, tabs=tabs + "\t")
        return target

    def branch_to_text(self):
        """
        Returns the branch and all of its children as text
        """
        if self._index is None:
            return ""
        target = ""
        for child in self.children:
            child: TextTreeNode
            target += self._branch_to_text(child, tabs="")
        return target

    def __str__(self):
        if self.is_root:
            return self.branch_to_text()
        else:
            return self.text


TreeFormatter = Callable[[TreeNode, Any, Any], str]
"Callback function which formats data to a string when rendering a tree"


@dataclass
class TextTreeBuilderOptions:
    """
    Defines the configuration for the building of a text tree from
    dictionaries, list and other Python collection classes.
    """

    @staticmethod
    def default_bullet_tree_formatter(
        node: TreeNode, value: Any, options: TextTreeBuilderOptions
    ) -> str:
        if isinstance(value, float):
            return f"{value:0.{options.precision}f}"
        return str(value)

    formatter: TreeFormatter = default_bullet_tree_formatter
    """
    Defines the formatter to be used. The formatter is called for every 
    element to allow custom conversion of the element to a string
    """
    flatten_lists: bool = True
    """
    Defines if lists of simple data types such as integers, floats and booleans
    shall be represented in a single line in one node rather than spread out.
    """
    max_flatten_size: int = 8
    """
    Defines the maximum size of a list that may be flattened.
    """
    precision: int = 2
    """
    Defines the default precision for floats
    """
    show_index: bool = False
    """
    Defines if the index of each list element shall be shown after it's
    bullet point.
    """
    identifier_prefix: str = ""
    """
    Defines the text to be added before each identifier
    """
    identifier_postfix: str = ": "
    """
    Defines the text to be added after each identifier
    """


class TextTree(TextTreeNode):
    """
    Helper class to a build a text tree which can be displayed in a document
    from other Python data classes such as lists or dictionaries.
    """

    @classmethod
    def _try_to_flatten(
        cls, node: TreeNode, element: Any, options: TextTreeBuilderOptions
    ) -> str | None:
        """
        Verifies if a list contains only simple data types such as integers,
        floats and bools which could be visualized in a single line and if
        so converts the list to a simple string.

        :param node: The node to which the data will be added
        :param element: The element to verify
        :param options: Options such as how large a list may be at max to be
            flattened.
        :return: A string containing the list's content on success, otherwise
            None.
        """
        if not isinstance(element, list) or not options.flatten_lists:
            return None
        if len(element) <= options.max_flatten_size:
            for entry in element:
                if not isinstance(entry, (float, bool, int)):
                    return None
        else:
            return None
        if options.formatter is not None:
            formatter = options.formatter
            return (
                "["
                + ", ".join([formatter(node, val, options) for val in element])
                + "]"
            )
        else:
            return "[" + ", ".join([str(val) for val in element]) + "]"

    @classmethod
    def _add_collection_to_tree(
        cls, node: TextTreeNode, element: dict | list, options: TextTreeBuilderOptions
    ) -> None:
        """
        Adds a collection such as a list or a dictionary to a TextTreeNode.

        :param node: The node to which the element and it's children shall
            be added.
        :param element: The element to add
        :param options: Creation options such as automatic flattening of
            shallow lists.
        """
        id_pre = options.identifier_prefix
        id_post = options.identifier_postfix
        if isinstance(element, dict):
            for key, value in element.items():
                if isinstance(value, list):
                    if (flat := cls._try_to_flatten(node, value, options)) is not None:
                        TextTreeNode(
                            f"{id_pre}{key}{id_post}{flat}", parent=node, name=key
                        )
                        continue
                if isinstance(value, (dict, list)):
                    new_node = TextTreeNode(
                        f"{id_pre}{key}{id_post}", parent=node, name=key
                    )
                    cls._add_collection_to_tree(new_node, value, options=options)
                else:
                    if options.formatter is not None:
                        value = options.formatter(node, value, options)
                    TextTreeNode(
                        f"{id_pre}{key}{id_post}{str(value)}", parent=node, name=key
                    )
        if isinstance(element, list):
            for index, value in enumerate(element):
                if options.show_index:
                    index_text = f"{id_pre}{index}{id_post}"
                else:
                    index_text = ""
                if isinstance(value, (dict, list)):
                    if (flat := cls._try_to_flatten(node, value, options)) is not None:
                        TextTreeNode(
                            f"{index_text}{flat}", parent=node, name=f"{index}"
                        )
                        continue
                    new_node = TextTreeNode(
                        f"{index_text}", parent=node, name=f"{index}"
                    )
                    cls._add_collection_to_tree(new_node, value, options=options)
                else:
                    if options.formatter is not None:
                        value = options.formatter(node, value, options)
                    TextTreeNode(
                        f"{index_text}{str(value)}", parent=node, name=f"{index}"
                    )

    @classmethod
    def from_collection(
        cls, collection: dict | list, options: TextTreeBuilderOptions | None = None
    ) -> TextTreeNode:
        """
        Converts a dictionary or a list to a nested bullet point list

        :param collection: The data element
        :param options: Defines how the single elements shall be converted to
            text form.
        :return: The root node - which can be visualized via str(root_node)
        """
        root_node = TextTree(text="/", name="root")
        if options is None:
            options = TextTreeBuilderOptions()
        TextTree._add_collection_to_tree(root_node, element=collection, options=options)
        return root_node
