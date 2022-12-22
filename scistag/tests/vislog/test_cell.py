"""
Tests the cell feature
"""
from scistag.vislog import VisualLog


def test_cell_creation():
    """
    Tests the general creation of a cell
    """
    log = VisualLog()
    vl = log.default_builder
    vp = log.default_page
    vl.title("Header")
    with vl.cell.begin() as cell:
        vl.log("Hello world")
    assert b"Hello world" in vp.render_element(None)[1]
    cell.clear()
    assert b"Hello world" not in vp.render_element(None)[1]
    with cell:
        vl.log("New content")
    assert b"New content" in vp.render_element(None)[1]
