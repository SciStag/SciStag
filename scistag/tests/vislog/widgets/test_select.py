"""
Tests the LSelect widget
"""
from scistag.vislog import VisualLog
from scistag.vislog.widgets import LSelect


def test_lselect_basic_setup():
    """
    Tests the basic initialization
    """
    log = VisualLog(fixed_session_id="tl")
    lb = log.default_builder
    elements = [
        "first",
        {"text": "second", "value": "second", "disabled": True},
        LSelect.Element(
            text="third",
            value="third",
            default=True,
            html_class="customClass",
            html_style="color:red",
        ),
        ("fourth", "fourth"),
    ]
    lb.test.checkpoint("insert_insert")
    sel = LSelect(lb, elements=elements)
    lb.test.assert_cp_diff("44f26b1e8265a4a4d4c9e136ed9dc957")
    assert sel.selected.value == "third"
    assert sel.value == "third"
    assert sel.get_value() == "third"
    sel.sync_value("third")
    assert sel.selected.value == "third"
    assert sel.element_by_value("any") is None
    assert sel.element_by_value("third") is elements[2]
    assert sel["third"] == elements[2]
    assert "any" not in sel
    assert "element0" in sel
    assert len(sel) == 4
    sel.sync_value(None)
    assert sel.get_value() == ""
    sel.sync_value("second")
    assert sel.get_value() == "second"
    sel.sync_value("")
    assert sel.get_value() == ""

    LSelect(lb, elements=[])  # test empty list

    lb.test.checkpoint("no_insert")
    sel = LSelect(lb, elements=elements, insert=False, default_index=1)
    assert sel.value == "second"
    lb.test.assert_cp_diff("d41d8cd98f00b204e9800998ecf8427e")
