"""
Implements the class :class:`Cell` which defines an either static or dynamic region
within the log or web page.

Each cell has its own isolated log data within the log which can either be completely
rebuilt in a given time interval or progressively extended.
"""

from __future__ import annotations

import time
from typing import Union, Callable

from scistag.vislog import VisualLogBuilder
from scistag.vislog.sessions.page_session import PageSession
from scistag.vislog.widgets import LWidget, LEvent

_LEVENT_TYPE_CELL_BUILD = "LEVENT_CELL_BUILD"
"Identifier for a cell rebuilt event"

DEFAULT_CELL_UPDATE_INTERVAL = 0.25
"The default update interval for cells if no other value is passed"


class CellBuildEvent(LEvent):
    """
    Event which is triggered when a cell shall rebuild
    """

    def __init__(self, *args, **kwargs):
        """
        :param args: Positiona arguments
        :param kwargs: Keyword arguments
        """
        super().__init__(event_type=_LEVENT_TYPE_CELL_BUILD, *args, **kwargs)


CellOnBuildCallback = Union[Callable[[], None], None]
"Callback function to be called when the cell shall be rebuild"


class Cell(LWidget):
    """
    The content cell defines a region within the log which can either be logged
    to surround a logical content area or for dynamic updating specific regions of
    the log.

    In HTML files it is represented with a div region.
    """

    def __init__(
        self,
        builder: VisualLogBuilder,
        interval_s: float | None = None,
        continuous: bool = False,
        progressive: bool = False,
        on_build: CellOnBuildCallback = None,
    ):
        """
        :param builder: The builder object we are attached to
        :param progressive: Defines if the cell and content shall be published
            progressive.

            This is good if you do not clear the cell and add logging data continuously
            to the log. If progressive is set to true the cell will not be cleared upon
            a build call.
        :param on_build: The callback to be called when the cell shall be build
        """
        builder.begin_update()
        name = builder.page_session.reserve_unique_name("cell", digits=4)
        builder.page_session.write_html(f'<div id="{name}">\n')
        super().__init__(builder=builder, name="cell", explicit_name=name)
        self.cell_name = name
        self.page_session.enter_element(self.sub_element)
        """The cell's unique name"""
        self._initial = True
        """Defines if this is the initial entering turn (which will add e.g. the
        div region to the html output)"""
        self._closed = False
        """Defines if the element was closed (left) already after it was entered"""
        self.on_build: CellOnBuildCallback = on_build
        """Function to be called when the cell shall be (re-)built"""
        self.progressive: bool = progressive
        """Defines if the update of the cell shall be published progressive or
        "in one go"."""
        self.interval_s = (
            interval_s if interval_s is not None else DEFAULT_CELL_UPDATE_INTERVAL
        )
        """The cell's interval in seconds.
        
        If continuous is set to True the cell will refresh itself in the interval
        defined, otherwise the maximum update frequency of updates 
        triggered via invalidate
        """
        self.continuous = continuous
        """If set to true the cell will update itself automatically within an interval
        of interval_s"""
        self._next_tick = None
        """The next tick at which the cell shall be updated"""
        self._last_invalidation = None
        """The time when the cell was invalidated the last time"""
        if self.interval_s is not None and self.continuous:
            self._next_tick = time.time() + self.interval_s

        self.build()

    def enter(self) -> Cell:
        """
        Enters the region and sets it as the page's new writing target

        :return: Self
        """
        if not self._initial:
            self.builder.begin_update()
            self.page_session.enter_element(self.sub_element)
            self._closed = False
        return self

    def leave(self) -> Cell:
        """
        Leaves the current cell after it was entered.

        :return Self:
        """
        if self._closed:
            return self
        self._closed = True
        if self._initial:
            self._initial = False
            self.page_session.end_sub_element()
            self.page_session.write_html(f"</div><!-- {self.cell_name} -->\n")
        else:
            self.page_session.end_sub_element()
        self.builder.end_update()
        return self

    def clear(self) -> Cell:
        """
        Clears the cells content

        :return: Self
        """
        self.sub_element.clear()
        return self

    def build(self):
        """
        Builds the cell's content
        """
        opened = self._closed
        if opened:
            self.enter()
        if not self.progressive:
            self.clear()
        self.sub_element.add_data("html", b'<div class="vl_log_cell">')
        self.handle_build()
        self.sub_element.add_data("html", b"</div>")
        if opened:
            self.leave()

    def handle_build(self):
        """
        Is called when ever the cell shall be (re)build.
        """
        if self.on_build is not None:
            self.on_build()

    def invalidate(self):
        """
        Invalidates the current cell and rebuilds it at the next update tick.

        The interval of the ticks is configured via the interval_s property.
        """
        if self._next_tick is None:
            cur_time = time.time()
            # if there was no recent update: update asap, otherwise limit
            # frequency to frequency_s
            self._next_tick = max(cur_time, self._last_invalidation + self.interval_s)
            self._last_invalidation = cur_time

    def handle_event(self, event: "LEvent"):
        """
        Handle incoming events

        :param event: The event to handle
        """
        if event.event_type == _LEVENT_TYPE_CELL_BUILD:
            self.build()

    def handle_loop(self) -> float | None:
        if self._next_tick is None:
            return None
        cur_time = time.time()
        if cur_time >= self._next_tick:
            self.build()
        if self.continuous:
            self._next_tick += self.interval_s
            self._next_tick = max(self._next_tick, cur_time)  # ensure no debt is build
        else:
            self._next_tick = None
        return self._next_tick

    def __enter__(self) -> Cell:
        return self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.leave()
