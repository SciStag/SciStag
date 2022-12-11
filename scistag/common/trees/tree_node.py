"""
Implements the :class:`TreeNode` class which helps to structure tree like data
such as folders or organizational structures.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TreeConfig:
    """
    Defines the tree's be
    """

    immutable: bool = False
    "Defines if the tree may be modified"
    create_missing: bool = True
    """
    If set to true a tree item will automatically be added if one tries to
    "access it via bracket operator and it does not exist yet
    """


class TreeNode:
    """
    The TreeNode class helps to structure data such as folder and file trees
    or to visualize nestable structures such as dictionaries containing lists
    containing dictionaries etd.
    """

    def __init__(self, name: str, parent: TreeNode = None):
        """
        :param name: The node's name. This name can be generic and is the
            leaf's or branch's unique identifier.
        :param parent: The parent node (if any)
        """
        self._name = name
        """
        The node's name - needs to be unique within the branch
        """
        if name is None or len(name) == 0:
            raise ValueError("A name needs to be provided")
        self._parent: TreeNode | None = None
        """
        The node's parent
        """
        self._index: dict[str, TreeNode] | None = None
        """
        The child index 
        """
        self.total_sub_node_count = 0
        """
        The total count of sub nodes including the children's children etc.
        """
        self.depth = 1
        """
        The tree's total depth
        """
        self.config: TreeConfig | None = None
        """
        The tree's configuration
        """
        if parent is not None:
            parent.add(self)
        else:
            self.config = TreeConfig()

    def add_empty(self, name: str, exist_ok: bool = False) -> TreeNode:
        """
        Adds an empty tree node of this node's class with given name
        of the list.

        :param name: The new leaf's name
        :param exist_ok: Do not fail but return the current entry if it already
            exists.
        :return: The leaf node
        """
        if self._index is not None and name in self._index:
            if exist_ok:
                return self._index[name]
            else:
                raise ValueError(
                    "Key already exists. Pass exist=ok to also "
                    "update already existing values"
                )
        return type(self)(name=name, parent=self)

    def __getitem__(self, item):
        """
        Returns a tree node by name.

        If the item does not exist and create_missing is set to true in
        the options will automatically be created with default parameters
        and added.

        :param item: The name of the item to search for
        :return: The item
        """
        if self._index is not None and item in self._index:
            return self._index[item]
        if self.config.immutable or not self.config.create_missing:
            raise KeyError(f"Element {str(item)} not found")
        if self._index is None:
            self._index = {}
        return type(self)(name=item, parent=self)

    def __len__(self):
        return len(self._index)

    def __contains__(self, item):
        return self._index is not None and item in self._index

    @property
    def name(self) -> str:
        """
        Returns the node's name
        """
        return self._name

    @property
    def is_leaf(self) -> bool:
        """
        Returns if this node is a leaf (a node without children)
        """
        return self._index is None or len(self._index) == 0

    @property
    def is_root(self) -> bool:
        """
        Is this node the root node?
        """
        return self._parent is None

    @property
    def parent(self) -> TreeNode | None:
        """
        The parent node of this leaf or branch
        """
        return self._parent

    @property
    def children(self) -> list[TreeNode]:
        """
        The children in the current branch
        """
        if self._index is None:
            return []
        return list(self._index.values())

    def add(self, node: TreeNode) -> None:
        """
        Adds a new tree node to this branch

        :param node: The node to be added
        """
        if self._index is None:
            self._index = {}
        if node._name in self._index:
            raise ValueError(f"A node with the name {node._name} already exists")
        self._index[node._name] = node
        node._parent = self
        node.config = self.config
        self._leaf_added(2)

    def _leaf_added(self, length=1) -> None:
        """
        Is called when ever a new (and potential future branch) is added

        :param length: The current depth
        """
        self.total_sub_node_count += 1
        self.depth = max(self.depth, length)
        if self._parent is not None:
            self._parent._leaf_added(length=length + 1)

    def __str__(self):
        return self._name

    def __iter__(self):
        return iter(self._index.items())
