"""
Tests the cell feature
"""
import time

from scistag.common.time import sleep_min
from scistag.vislog import VisualLog
from scistag.vislog.widgets.timer import LTimerTickEvent


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
    cell.leave()  # twice, just for testing
    assert b"Hello world" in vp.render_element(None)[1]
    cell.clear()
    assert b"Hello world" not in vp.render_element(None)[1]
    with cell:
        vl.log("New content")
    assert b"New content" in vp.render_element(None)[1]


def test_cell_updating():
    """
    Tests the automatic update of cells e.g. through timers
    """
    log = VisualLog()
    vl = log.default_builder
    vp = log.default_page
    vl.title("Header")

    counter = 0
    once_counter = 0
    counter_prog = 0

    def count_on():
        nonlocal counter, vl
        vl.log(f"CellBuild {counter}")
        counter += 1

    def count_on_prog():
        nonlocal counter_prog, vl
        vl.log(f"CellBuildProg {counter_prog}")
        counter_prog += 1

    def count_on_once():
        nonlocal once_counter, vl
        vl.log(f"CellBuildOnce {once_counter}")
        once_counter += 1

    cell = vl.cell.add(interval_s=0.05, continuous=True, on_build=count_on)
    cell_prog = vl.cell.add(
        interval_s=0.05, continuous=True, on_build=count_on_prog, progressive=True
    )
    cell_once = vl.cell.add(interval_s=0.05, continuous=False, on_build=count_on_once)
    cell.invalidate()
    cell_once.invalidate()
    assert b"CellBuild 0" in vp.render_element()[1]
    assert b"CellBuildOnce 0" in vp.render_element()[1]
    assert b"CellBuildProg 0" in vp.render_element()[1]
    sleep_min(0.05)
    vl.widget.handle_event_list()
    vl.widget.handle_event_list()
    assert b"CellBuild 1" in vp.render_element()[1]
    assert b"CellBuildOnce 1" in vp.render_element()[1]
    cell.build()  # build explicitly
    cell_prog.build()
    rendering = vp.render_element()[1]
    assert b"CellBuild 2" in rendering and b"CellBuild 1" not in rendering
    assert b"CellBuildProg 2" in rendering and b"CellBuildProg 1" in rendering
    sleep_min(0.05)
    vl.widget.handle_event_list()
    assert b"CellBuildOnce 1" in vp.render_element()[1]
    # trigger unknown event
    cell.handle_event(LTimerTickEvent(name=cell.name, widget=cell))
