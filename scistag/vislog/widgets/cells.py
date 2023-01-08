"""
Implements the class :class:`Cell` which defines an either static or dynamic region
within the log or web page.

Each cell has its own isolated log data within the log which can either be completely
rebuilt in a given time interval or progressively extended.
"""

from __future__ import annotations

import time
from inspect import signature
from typing import Union, Callable

from scistag.vislog import LogBuilder
from scistag.vislog.widgets import LWidget, LEvent

_LEVENT_TYPE_CELL_BUILD = "LEVENT_CELL_BUILD"
"Identifier for a cell rebuilt event"

DEFAULT_CELL_UPDATE_INTERVAL = 0.1
"The default update interval for cells if no other value is passed"


class LCellBuildEvent(LEvent):
    """
    Event which is triggered when a cell shall rebuild
    """

    def __init__(self, *args, **kwargs):
        """
        :param args: Positiona arguments
        :param kwargs: Keyword arguments
        """
        super().__init__(event_type=_LEVENT_TYPE_CELL_BUILD, *args, **kwargs)


CellOnBuildCallback = Union[Callable[[], None], Callable[[LogBuilder], None], None]
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
        builder: LogBuilder,
        interval_s: float | None = None,
        continuous: bool = False,
        progressive: bool = False,
        static: bool = False,
        groups: str | list[str] = None,
        uses: str | list[str] = None,
        requires: str | list[str] = None,
        tab: str | None = None,
        page: int | None = None,
        data_cell: bool = False,
        on_build: CellOnBuildCallback = None,
        _builder_method: Union[Callable, None] = None,
    ):
        """
        :param builder: The builder object we are attached to
        :param progressive: Defines if the cell and content shall be published
            progressive.

            This is good if you do not clear the cell and add logging data continuously
            to the log. If progressive is set to true the cell will not be cleared upon
            a build call.
        :param static: Defines if the cell is static and does not need any container
            when being stored in the html file.
        :param uses: A list of cache and file names which shall be observed. If any of
            the elements does change the cell will be invalidated.
        :param requires: A list of cache and file names which are required. Like uses
            the cell will be refreshed if the value changes but in addition the cell
            also won't be build at all before the value or file is present.
        :param groups: A list of visibility groups the page is attached to.
        :param tab: The tab in which the cell shall be displayed. If a tabe is defined
            in the LogBuilder (by default it is not) only cells with the associated tab
            or None  will be displayed. IF tab and page are defined the hierarchy is
            tab>page.
        :param data_cell: If set the cell wi
        :param page: The cell's page index. If a page is defined in the LogBuilder
            (by default it is not) only cells with the associated page or None will be
            displayed.
        :param data_cell: If set the cell will be flagged as pure data cell w/o visual
            content and thus no required updates after a rebuild.
        :param on_build: The callback to be called when the cell shall be build
        :param _builder_method: The object method to which this cell is attached
        """
        if _builder_method is not None:
            _builder_method.__dict__["cell"] = self
            _builder_method.__dict__["invalidate"] = lambda cell=self: cell.invalidate()
            builder.cell[_builder_method.__name__] = self
        builder.begin_update()
        name = builder.page_session.reserve_unique_name("cell", digits=4)
        if not static:
            builder.page_session.write_html(f'<div id="{name}" class="vl_log_cell">\n')
        super().__init__(builder=builder, name="cell", explicit_name=name)
        self.cell_name = name
        self.groups = {"default"}
        if groups is not None:
            if isinstance(groups, str):
                self.groups.add(groups)
            else:
                self.groups = self.groups.union(set(groups))
        self.uses = set()
        if uses is not None:
            if isinstance(uses, str):
                self.uses.add(uses)
            else:
                self.uses = self.uses.union(set(uses))
        self.requires = set()
        if requires is not None:
            if isinstance(requires, str):
                self.requires.add(requires)
            else:
                self.requires = self.requires.union(set(requires))
        self.tab = tab
        """
        Define on which tab the cell shall be visible. Will automatically add the
        cell to a group named t{tab} if just the tab is specified or t{tab}.page{} if
        tab and page are defined"""
        self.page = page
        """
        Define on which page the cell shall be visible. Will automatically add the
        cell to a group named p{page} if just the tab is specified or t{tab}.page{} if
        tab and page are defined"""
        if self.tab:
            self.groups.add(f"tab_{tab}")
        if self.page:
            self.groups.add(f"page_{page}")
        self.data_cell = data_cell
        """Defines if this is a data cell which causes no direct visual modifications
        and thus does not need to trigger a client site view refresh"""
        self.page_session.enter_element(self.sub_element)
        """The cell's unique name"""
        self._initial = True
        """Defines if this is the initial entering turn (which will add e.g. the
        div region to the html output)"""
        self._closed = False
        """Defines if the element was closed (left) already after it was entered"""
        self.static = static
        """Defines if the cell is static and can not be individually modified"""
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
        self._last_invalidation = time.time()
        """The time when the cell was invalidated the last time"""
        if self.interval_s is not None and self.continuous:
            self._next_tick = time.time() + self.interval_s
        self.hashes = {}
        """Stores the hash values for all observed elements"""
        self.build()
        self.leave()
        if not static:
            self.page_session.write_html(f"</div><!-- {self.cell_name} -->\n")

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
        self.sub_element.flags["widget"] = self
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
        if self.can_build:
            if not self.progressive:
                self.sub_element.add_data("html", b"<div>")
            event = LCellBuildEvent(
                name=self.identifier, widget=self, builder=self.builder
            )
            self.raise_event(event)
            if not self.progressive:
                self.sub_element.add_data("html", b"</div>")
        if opened:
            self.leave()
        self.update_hashes()

    @property
    def can_build(self):
        """
        Returns if all of the cell's requirements are fulfilled and it can be build
        """
        for key in self.requires:
            if key not in self.builder.cache:
                return False
        return True

    def update_hashes(self):
        """
        Updates the hashes of the last modification
        """
        element_set = self.uses.union(self.requires)
        for key in element_set:
            self.hashes[key] = self.builder.cache.get_version(key)

    def handle_build(self):
        """
        Is called when ever the cell shall be (re)build.
        """
        if self.on_build is not None:
            sig = signature(self.on_build)
            if len(sig.parameters):
                self.on_build(self.builder)
            else:
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
            self.handle_build()

    def handle_loop(self) -> float | None:
        cur_time = time.time()
        element_set = self.uses.union(self.requires)
        for key in element_set:
            hash_val = self.builder.cache.get_version(key)
            if hash_val != self.hashes.get(key, 0):
                self._next_tick = cur_time
        if self._next_tick is None:
            return None
        if cur_time >= self._next_tick:
            self.build()
        else:
            return self._next_tick
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
