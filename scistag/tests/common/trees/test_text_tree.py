"""
Tests the TextTree class which shall help building simple text based trees
such as bullet lists in documents
"""
import hashlib

from scistag.common.trees import TextTreeNode, TextTreeBuilderOptions, TextTree


def test_basic_text_tree():
    """
    Tests the basic text tree functionality
    """
    root_node = TextTreeNode(name="/", text="")
    assert root_node.branch_to_text() == ""
    root_node["first"].text = "first"
    root_node.add(TextTreeNode("second", "second"))
    root_node.add_empty("third").text = "third"
    text = root_node.branch_to_text()
    hash_val = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
    assert hash_val == 183531075463811948955827356922084374834

    options = TextTreeBuilderOptions()
    long_int_list = [value for value in range(options.max_flatten_size + 1)]
    assert TextTree._try_to_flatten(root_node, long_int_list, options=options) is None
    short_int_list = [value for value in range(options.max_flatten_size - 1)]
    assert (
        TextTree._try_to_flatten(root_node, short_int_list, options=options) is not None
    )
    options.formatter = None
    options.show_index = True
    assert (
        TextTree._try_to_flatten(root_node, short_int_list, options=options) is not None
    )
    _ = str(TextTree.from_collection(long_int_list, options=options))
    _ = str(TextTree.from_collection(short_int_list, options=options))

    # further full tests of this class are executed in the tests of
    # VisualLog.collections
