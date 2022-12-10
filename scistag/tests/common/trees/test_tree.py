"""
Testing tree basics
"""
import pytest

from scistag.common.trees import TreeNode


def test_tree_basics():
    """
    Test TreeNode
    """
    with pytest.raises(ValueError):
        TreeNode(name="")
    with pytest.raises(ValueError):
        TreeNode(name=None)

    base_node = TreeNode("/")
    _ = base_node["sub"]
    assert "sub2" not in base_node
    assert "sub" in base_node
    assert base_node.total_sub_node_count == 1
    man_sub_node = TreeNode("man")
    base_node.add(man_sub_node)
    assert "man" in base_node
    assert base_node.depth == 2
    assert base_node["sub"].is_leaf
    _ = base_node["sub"]["sub_sub"]
    assert not base_node["sub"].is_leaf
    assert base_node.depth == 3
    _ = base_node["sub"]["sub_sub"]["sub_sub_sub"]
    assert base_node.depth == 4
    base_node.config.immutable = True
    with pytest.raises(KeyError):
        _ = base_node["sub"]["sub_subx"]
    base_node.config.immutable = False
    assert base_node["sub"] is base_node.add_empty("sub", exist_ok=True)
    with pytest.raises(ValueError):
        base_node.add_empty("sub", exist_ok=False)
    new_node = base_node.add_empty("new")
    assert new_node.name == "new"
    assert new_node.parent == base_node
    assert len(base_node) == 3
    assert base_node.total_sub_node_count == 5
    with pytest.raises(ValueError):
        base_node.add(TreeNode("new"))
    rlist = [element for element in base_node]
    assert len(rlist) == 3
    assert str(base_node) == "/"
    _ = base_node["sub2"]
    assert "sub2" in base_node
