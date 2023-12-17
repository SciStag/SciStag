"""
Implements the class :class:`Cell` which defines an either static or dynamic region
within the log or web page.

Each cell has its own isolated log data within the log which can either be completely
rebuilt in a given time interval or progressively extended.
"""

from __future__ import annotations

import io
import time
from contextlib import redirect_stdout
from fnmatch import fnmatch
from inspect import signature
from typing import Union, Callable

from pydantic import BaseModel

from scistag.vislog import LogBuilder
from scistag.vislog.widgets import LWidget, LEvent

CELL_TYPE_SIMPLE = "simple"
"Defines a basic cell without any further decoration"

CELL_TYPE_SECTION = "section"
"""Defines a section which is visually splitted with a horizontal line, optionally 
also with title"""

CELL_TYPE_DATA = "data"
"Defines a data cell which does not produce visual output but just data"

CELL_TYPE_ONCE = "once"
"Defines a data cell whose build function is guaranteed to be called once"

CELL_TYPE_STREAM = "stream"
"""Defines a data cell which processes stream data or data provided via cache 
modifications"""

CELL_REQUIREMENTS_ZERO_SIZE_CHECK_POSTFIX = ">0"
"""Postfix which can be added to a cell's requirement key names to only count them
as valid if they are not zero, not None or contain at least one list element"""

CELL_REQUIREMENTS_EQUAL = "=="
"""Comparison flag to compare a cache variable with a certain value"""

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


class CellStats(BaseModel):
    """
    Contains statistics about the cell
    """

    builds: int = 0
    """The total build count"""
    bps: float = 0.0
    """Builds per second"""
    total_build_time_s: float = 0.0
    """The total amount of time required for builds in seconds"""
    avg_build_time_s: float = 0.0
    """The average time required to build the cell in seconds"""
    build_time_s: float = 0.0
    """The last amount of time required to build the cell in seconds"""


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
        name: str | None = None,
        section: str | None = None,
        interval_s: float | None = None,
        continuous: bool = False,
        progressive: bool = False,
        static: bool = False,
        groups: str | list[str] = None,
        uses: str | list[str] = None,
        output: str | list[str] = None,
        requires: str | list[str] = None,
        page: int | str | None = None,
        capture_stdout: bool = False,
        ctype: str | None = None,
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
        :param output: A list of cache and file names which are generated by this cell.
        :param requires: A list of cache and file names which are required. Like uses
            the cell will be refreshed if the value changes but in addition the cell
            also won't be build at all before the value or file is present.
        :param groups: A list of visibility groups the page is attached to.
        :param ctype: Defines the cell's type.

            Supported types are:
            - "seamless" - for a default cell w/o any decorations
            - "section" - for a cell which inserts a spacing to previous cells of the same
                type.
            - "data" - for cells which do just create data and do not need to be displayed
            - "snippet" - Defines a cell which is not displayed by itself but can be
                inserted, e.g. into inserted documents via {{SNIPPET_NAME}}

            By default "seamless" will be selected except a section title was defined.
        :param page: The cell's page index. If a page is defined in the LogBuilder
            (by default it is not) only cells with the associated page or None will be
            displayed.
        :param capture_stdout: Defines if the stdout shall be captured and added to
            the log, e.g. print calls.
        :param on_build: The callback to be called when the cell shall be build
        :param _builder_method: The object method to which this cell is attached
        """
        if _builder_method is not None:
            _builder_method.__dict__["cell"] = self
            _builder_method.__dict__["invalidate"] = lambda cell=self: cell.invalidate()
            builder.cell[_builder_method.__name__] = self
        builder.begin_update()
        gen_name = builder.page_session.reserve_unique_name("cell", digits=4)
        if ctype is not None and ctype in [
            CELL_TYPE_DATA,
            CELL_TYPE_ONCE,
            CELL_TYPE_STREAM,
        ]:
            static = True
        if not static:
            builder.page_session.write_html(
                f'<div id="{gen_name}" class="vl_log_cell">\n'
            )
        super().__init__(builder=builder, name="cell", explicit_name=gen_name)
        self.cell_name = gen_name
        self.name = name
        if groups is not None:
            if isinstance(groups, str):
                self.groups = {groups}
            else:
                self.groups = self.groups = set(groups)
        else:
            self.groups = {"default"}
        self.uses = set()
        if uses is not None:
            if isinstance(uses, str):
                self.uses.add(uses)
            else:
                self.uses = self.uses.union(set(uses))
        self.output = set()
        if output is not None:
            if isinstance(output, str):
                self.output.add(output)
            else:
                self.output = self.output.union(set(output))
        self.requires = set()
        if requires is not None:
            if isinstance(requires, str):
                self.requires.add(requires)
            else:
                self.requires = self.requires.union(set(requires))
        self.page = page
        """
        Define on which page the cell shall be visible. Will automatically add the
        cell to a group named p{page} if just the tab is specified or t{tab}.page{} if
        tab and page are defined"""
        self.section_name = section
        """The section name to be displayed before the section"""
        if ctype is None:
            if section is not None:
                ctype = CELL_TYPE_SECTION
            else:
                ctype = CELL_TYPE_SIMPLE
        self.ctype = ctype
        """Defines if this is a data cell's type and how it shall visually appear.
        
        See :class:`Cell`"""
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
        self.statistics = CellStats()
        """
        Cell specific stats like updates, updates per second etc.
        """
        self.statistics_update_interval_s = 2.0
        """Defines how often the cell's statistics are updated"""
        self._last_stats_update = time.time()
        """Time of last stats update"""
        self._last_stats_counter = 0
        """Build counter at last stats update"""
        self._build_time_acc = 0.0
        """Accumulated time for builds since the last reset"""
        self.capture_stdout = capture_stdout
        """Defines if elements logged via print() shall be logged into the cell"""
        self.could_build = False
        """Defines if the cell could be build the last time"""
        self._data_dependencies: dict[str, int] = {}
        """Defines which dependencies this element used and which hash they had"""
        self.build()
        self.leave()
        if not static:
            self.page_session.write_html(f"</div><!-- {self.cell_name} -->\n")

    def enter(self) -> Cell:
        """
        Enters the region and sets it as the page's new writing target

        :return: Self
        """
        assert not self._initial
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
            self.clear_dependencies()
            self.could_build = True
            start_time = time.time()
            old_mod = self.sub_element.last_direct_change_time
            if not self.progressive and not self.static:
                self.sub_element.add_data("html", b"<div>\n")
            if not self.progressive:
                self.render_header()
            event = LCellBuildEvent(
                name=self.identifier, widget=self, builder=self.builder
            )
            std_out = io.StringIO()
            if self.capture_stdout:
                with redirect_stdout(std_out):
                    self.raise_event(event)
            else:
                self.raise_event(event)
            buffer = std_out.getvalue()
            if len(buffer) > 0:
                self.handle_stdout(buffer)
            if not self.progressive:
                self.render_footer()
            if not self.progressive and not self.static:
                self.sub_element.add_data("html", b"</div>\n")
            if self.ctype in [CELL_TYPE_DATA, CELL_TYPE_ONCE, CELL_TYPE_STREAM]:
                # prevent visual updates through a data cell
                self.clear()
                self.sub_element.last_direct_change_time = old_mod
            time_required = time.time() - start_time
            self.statistics.build_time_s = time_required
            self._build_time_acc += time_required
            self.statistics.builds += 1
        else:
            self.could_build = False
        if opened:
            self.leave()
        self.update_hashes()

    def render_header(self):
        """
        Adds the cell's header elements
        """
        if self.ctype == CELL_TYPE_SECTION:
            self.builder.br().hr(self.section_name).add_html("\n")

    def render_footer(self):
        """
        Adds the cell's footer elements
        """

    @property
    def can_build(self):
        """
        Returns if all the cell's requirements are fulfilled, and it can be build
        """
        for key in self.requires:
            real_key = key
            if real_key.endswith(CELL_REQUIREMENTS_ZERO_SIZE_CHECK_POSTFIX):
                real_key = self._clean_key_name(real_key)
                if not self.builder.cache.non_zero(real_key):
                    return False
            elif CELL_REQUIREMENTS_EQUAL in real_key:
                if not self.builder.cache.eval(real_key):
                    return False
            else:
                if key not in self.builder.cache:
                    return False
        if self.ctype == CELL_TYPE_ONCE and self.statistics.builds > 0:
            return False
        return self.may_be_shown()

    def may_be_shown(self) -> bool:
        """
        Returns if the cell is not hidden or included by any visibility flags such as
        its groups, page or tab

        :return: True if the cell can be painted in general, independent of data
            dependencies.
        """
        if self.page is not None:  # verify page - if one is set
            cp = self.builder.current_page
            if cp == "" or cp != self.page:
                return False
        included: bool = False
        for group in self.builder.visible_groups:
            for own_group in self.groups:
                if fnmatch(own_group, group):
                    included = True
                    break
        if not included:
            return False
        for group in self.builder.hidden_groups:
            for own_group in self.groups:
                if fnmatch(own_group, group):
                    return False
        return True

    def update_hashes(self):
        """
        Updates the hashes of the last modification
        """
        element_set = self.uses.union(self.requires)
        for key in element_set:
            key = self._clean_key_name(key)
            self.hashes[key] = self.builder.cache.get_revision(key)

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
        if cur_time - self._last_stats_update > self.statistics_update_interval_s:
            time_diff = cur_time - self._last_stats_update
            count_diff = self.statistics.builds - self._last_stats_counter
            self.statistics.bps = count_diff / time_diff
            self._last_stats_counter = self.statistics.builds
            self._last_stats_update = cur_time
            self.statistics.total_build_time_s += self._build_time_acc
            self.statistics.avg_build_time_s = (
                self._build_time_acc / count_diff if count_diff > 0 else 0.0
            )
            self._build_time_acc = 0.0

        if self.detect_changes():
            self._next_tick = cur_time
        if self.could_build != self.can_build:  # check if the visibility changed
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

    def detect_changes(self):
        """
        Is called in intervals to detect changes in used cache variables or tracked
        data sources.
        """
        element_set = self.uses.union(self.requires)
        for key in element_set:
            key = self._clean_key_name(key)
            hash_val = self.builder.cache.get_revision(key)
            if hash_val != self.hashes.get(key, 0):
                return True
        for element in self._data_dependencies:
            cur_hash = self._data_dependencies[element]
            new_hash = self.builder.data_loader.get_hash(element)
            if new_hash is None or cur_hash != new_hash:
                return True
        return False

    def handle_stdout(self, buffer: str):
        """
        Is called when options.console.mode is set to "record" or "mirror" when
        console output data was collected due to direct usage of the **print** method.

        :param buffer: The data buffer
        """
        self.builder.log(buffer)

    def __enter__(self) -> Cell:
        return self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.leave()

    def log_statistics(self):
        """
        Adds statistics about the VisualLog as table to the log
        """
        statistics = self.statistics
        uptime = time.time() - self.builder.stats.start_time
        self.builder.table(
            [
                ["Updates", f"{statistics.builds} " f"total updates"],
                ["Effective fps", f"{statistics.bps:0.2f} updates per second"],
                ["Build time", f"{statistics.build_time_s:0.2f} s"],
                ["Uptime", f"{uptime:0.2f} seconds"],
            ],
            index=True,
        )

    @staticmethod
    def _clean_key_name(key: str) -> str:
        """
        Removes statements from requirement keys

        :param key: The key
        :return: The cleaned key name to hash
        """
        if key.endswith(CELL_REQUIREMENTS_ZERO_SIZE_CHECK_POSTFIX):
            return key[0 : -len(CELL_REQUIREMENTS_ZERO_SIZE_CHECK_POSTFIX)]
        if CELL_REQUIREMENTS_EQUAL in key:
            values = key.split(CELL_REQUIREMENTS_EQUAL)
            return values[0]
        return key

    def clear_dependencies(self):
        """
        Clears all current dependencies
        """
        self._data_dependencies = {}
        self.builder.data_loader.handle_cell_modified(self)

    def add_data_dependency(self, source: str):
        """
        Adds a data dependency to the cell for automatic cache clearance and
        triggering the auto-reloader (if enabled) when an included data source gets
        modified.

        :param source: The name of the file which shall be tracked. By
            default only local files are observed.
        """
        self.builder.data_loader.add_source(source, self)
        if source not in self._data_dependencies:
            self._data_dependencies[source] = self.builder.data_loader.get_hash(source)
