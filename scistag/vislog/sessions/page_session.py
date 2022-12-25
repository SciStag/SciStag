"""
Implements :class:`PageSession` which stores the content of a single user's page
and provides methods to modify and extend this content.
"""
from __future__ import annotations

import time
from typing import Union, TYPE_CHECKING, Callable
from collections import Counter

from scistag.common import StagLock
from scistag.filestag import FileStag
from scistag.vislog.common.log_element import LogElement, LogElementReference

ROOT_DOM_ELEMENT = "vlbody"
"Defines the root element in the HTML page containing the main site's data"

# Definition of output types
HTML = "html"
"Html output"
CONSOLE = "console"
"Console output"
TXT = "txt"
"Txt output"
MD = "md"
"Markdown output"

ROOT_ELEMENT_NAME = "vlbody"
"""Defines the name of a page's root element"""

if TYPE_CHECKING:
    from scistag.vislog.visual_log import VisualLog
    from scistag.vislog.common.page_update_context import PageUpdateContext
    from scistag.vislog import VisualLogBuilder


class PageSession:
    """
    Holds the data content of a single page for a single user/browser session and
    provides methods to write just this content
    """

    def __init__(
        self,
        log: "VisualLog",
        builder: Union["VisualLogBuilder", None],
        log_formats: set[str],
        index_name: str,
        target_dir: str,
        continuous_write: bool,
        log_to_stdout: bool,
        log_to_disk: bool,
    ):
        """
        :param log: The target log instance
        :param builder: The log builder instance
        :param log_formats: The supported logging formats as string set
        :param index_name: The name of the index file
        :param target_dir: The target directory
        :param continuous_write: Defines if modifications shall directly be written
            to disk so no data is lost if e.g. the application or script crashes
        :param log_to_stdout: Defines if logging shall be forwarded to the stdout
            console
        :param log_to_disk: Defines if the content shall be written to disk
        """
        self.log_formats: set[str] = log_formats
        """Defines the list of supported formats"""
        self.log: "VisualLog" = log
        """The target log instance"""
        self.builder: Union["VisualLogBuilder", None] = builder
        """The builder which is used to create the page's content"""
        self._logs = LogElement(
            name=ROOT_ELEMENT_NAME, output_formats=sorted(self.log_formats)
        )
        """
        Defines the single log elements
        """
        self._log_backup: LogElement | None = None
        """
        Defines a copy of the current data
        """
        self.target_dir = target_dir
        """
        The target output directory
        """
        self._page_lock = StagLock()
        "Lock for multithread secure access to the latest page update"
        self._backup_lock = StagLock()
        "Lock for multithread secure access to the latest page update backup"
        self.cur_element: LogElement = self._logs
        """Defines the current target element"""
        self.element_stack: list[LogElement] = []
        """Stag of previous elements which were previously a target"""
        self._html_export = HTML in self.log_formats
        "Defines if HTML gets exported"
        self.md_export = MD in self.log_formats
        "Defines if markdown gets exported"
        self.txt_export = TXT in self.log_formats
        "Defines if txt gets exported"
        self.index_name = index_name
        "Defines the log's index file name"
        self._txt_filename = self.target_dir + f"/{self.index_name}.txt"
        "The name of the txt file to which we shall save"
        self.html_filename = self.target_dir + f"/{self.index_name}.html"
        "The name of the html file to which we shall save"
        self._md_filename = self.target_dir + f"/{self.index_name}.md"
        "The name of the markdown file to which we shall save"
        self.continuous_write = continuous_write
        self.log_to_stdout = log_to_stdout
        self.log_to_disk = log_to_disk
        self._page_backups: dict[str, bytes] = {}
        """
        A backup of the latest rendered page of each dynamic data type
        (excluding PDFs and PNGs which are just created on demand)
        """
        self._body_backups: dict[str, bytes] = {}
        """
        A backup of the latest body renderings for each content type
        """
        self.name_counter = Counter()
        "Counter for file names to prevent writing to the same file twice"
        self.title_counter = Counter()
        "Counter for titles to numerate the if appearing twice"
        self._update_context_counter = 0
        """Defines if the page is currently in an updating state.         
        See :meth:`begin_update`"""
        self.last_client_id: str = ""
        """The client's ID the last time it requested events"""
        self.element_update_times: dict[str, float] = {}
        """Contains for every element the time stamp when it was updated the last 
        time"""
        self.old_client_ids: set[str] = set()
        """Previously connected client IDs"""
        self.next_event_time = time.time()
        """The timestamp at which we think the next event will occur"""
        self.minimum_refresh_time = 0.01
        """The lowest allowed refresh time in seconds"""
        self._event_target_page: PageSession | None = None
        """Page to which all events shall be forwarded. Required if the page is
        embedded in another lock, e.g. when using an auto reloader"""

    def create_log_backup(self):
        """
        Creates a copy of the logs and stores it in the log backup
        """
        with self._page_lock:
            log_copy = self._logs.clone()
        with self._backup_lock:
            self._log_backup = log_copy

    def write_html(self, html_code: str | bytes):
        """
        The HTML code to add

        :param html_code: The html code
        :return: True if txt logging is enabled
        """
        if HTML not in self.log_formats:
            return
        if not isinstance(html_code, bytes):
            html_code = html_code.encode("utf-8")
        self.cur_element.add_data(HTML, html_code)
        if self.continuous_write:
            self.write_to_disk(formats={HTML})
        return True

    def write_md(self, md_code: str, no_break: bool = False):
        """
        The markdown code to add

        :param md_code: The markdown code
        :param no_break: If defined no line break will be added
        :return: True if txt logging is enabled
        """
        if MD not in self.log_formats:
            return
        new_text = md_code + ("" if no_break else "\n")
        self.cur_element.add_data(MD, new_text.encode("utf-8"))
        if self.continuous_write:
            self.write_to_disk(formats={MD})
        return True

    def write_txt(self, txt_code: str, console: bool = True, md: bool = False):
        """
        Adds text code to the txt / console log

        :param txt_code: The text to add
        :param console: Defines if the text shall also be added ot the
            console's log (as it's mostly identical). True by default.
        :param md: Defines if the text shall be added to markdown as well
        :return: True if txt logging is enabled
        """
        if self.log_to_stdout:
            print(txt_code)
        if console and len(self.log._consoles):
            self._add_to_console(txt_code)
        if md and MD in self.log_formats:
            self.write_md(txt_code)
        if TXT not in self.log_formats:
            return
        self.cur_element.add_data(TXT, (txt_code + "\n").encode("utf-8"))
        if self.continuous_write:
            self.write_to_disk(formats={TXT})
        return True

    def _add_to_console(self, txt_code: str):
        """
        Adds text code to the console log

        :param txt_code: The text to add
        :return: True if txt logging is enabled
        """
        for console in self.log._consoles:
            if console.progressive:
                console.print(txt_code)
        self.cur_element.add_data(CONSOLE, (txt_code + "\n").encode("ascii"))
        return True

    def _build_body(self):
        """
        Requests to combine all logs and sub logs to a single page which
        can be logged to the disk or provided in the browser. (excluding
        html headers and footers), so just "the body" of the HTML page.

        :return: The finalized page, e.g. by combining base_log w/
            sub_logs as shown in the :class:`VisualLiveLog` class.
        """
        body: dict[str, bytes] = {}

        for cur_format in self.log_formats:
            log_data = self._logs.build(cur_format)

            if cur_format == HTML:
                body[cur_format] = self.log._renderers[HTML].build_body(log_data)
            else:
                body[cur_format] = log_data
        return body

    def set_latest_page(self, page_type: str, content: bytes):
        """
        Stores a copy of the latest page.

        This method is multi-threading secure.

        :param page_type: The format of the page to store
        :param content: The page's new content
        """
        with self._page_lock:
            self._page_backups[page_type] = content

    def get_page(self, format_type: str) -> bytes:
        """
        Receives the newest update of the page of given output type.

        If not done automatically (e.g. when using a VisualLiveLog)
        you might have to call render_pages yourself.

        This method is multi-threading secure.

        Assumes that render() or write_to_disk() or render was called before
        since the last change. This is not necessary if continuous_write is
        enabled.

        :param format_type: The type of the page you want to receive
        :return: The page's content.
        """
        with self._page_lock:
            self.last_page_request = time.time()
            if format_type in self._page_backups:
                return self._page_backups[format_type]
            return b""

    def get_root_element(self, backup: bool | None = None) -> (StagLock, LogElement):
        """
        Returns the current, active root element and it's access lock
        :param backup: Defines if the backup or default element shall be used.

            Will be auto-detected if None is passed.
        :return: The access lock to access the content, the root element
        """
        if backup is None:
            with self._backup_lock:
                backup = self._update_context_counter >= 1
        if backup:
            return self._backup_lock, self._log_backup
        else:
            return self._page_lock, self._logs

    def render_element(
        self,
        name: str | None = None,
        output_format: str = HTML,
        backup: bool | None = None,
    ) -> (float, bytes):
        """
        Returns the element at given node, starting with the root element
        ROOT_ELEMENT_NAME

        :param name: The name of the element to return.

            By default the root element will be returned.
        :param output_format: The format to return
        :param backup: Defines if the last backup shall be accessed rather than the
            working data. If no value is passed the mode will be automatically selected.
        :return: Timestamp of the last update, the element's content
        """
        if name is None:
            name = ROOT_ELEMENT_NAME
        cleaned_name = name.replace("-", ".")
        tree = cleaned_name.split(".")
        if len(tree) == 0 or tree[0] != ROOT_ELEMENT_NAME:
            return 0.0, b""

        access_lock, element = self.get_root_element(backup)

        with access_lock:
            for cur_sub_name in tree[1:]:
                if cur_sub_name in element:
                    element = element[cur_sub_name]
                else:
                    return 0.0, b""
            latest_update = max(
                element.last_child_update_time, element.last_direct_change_time
            )
            return latest_update, element.build(output_format)

    def get_body(self, format_type: str = HTML) -> bytes:
        """
        Returns the latest body data.

        Contains only the part of that format w/ header and footer.
        Can be used to for example embed one log's content in another log
        such as main_log.html(sub_log.get_body("html"))

        Assumes that render() or write_to_disk() or render was called before
        since the last change. This is not necessary if continuous_write is
        enabled.

        :param format_type: The type of the page you want to receive
        :return: The page's content.
        """
        with self._page_lock:
            if format_type in self._body_backups:
                return self._body_backups[format_type]
            return b""

    def render(self, formats: set[str] | None = None) -> PageSession:
        """
        Renders all pages - so combines the main log with the sub logs
        of the supported output types (html, txt, md etc.) and stores
        them.

        The page data for each type can be received via :meth:`get_latest_page`.

        :param formats: A set of the formats which shall be rendered.

            None = All configured formats.
        :return: The VisualLog object
        """
        if formats is None:
            formats = self.log_formats
        bodies = self._build_body()
        with self._page_lock:
            self._body_backups = bodies
        # store html
        if HTML in formats:
            self.set_latest_page(
                HTML, self.log._renderers[HTML].build_page(bodies[HTML])
            )
        # store markdown
        if MD in formats:
            self.set_latest_page(MD, bodies[MD])
        # store txt
        if TXT in formats:
            self.set_latest_page(TXT, bodies[TXT])
        if CONSOLE in formats:
            for console in self.log._consoles:
                if console.progressive:
                    continue
                console.clear()
                body = bodies[CONSOLE]
                console.print(body.decode("ascii"))
        return self

    def write_to_disk(
        self, formats: set[str] | None = None, render=True
    ) -> PageSession:
        """
        Writes the rendered pages from all (or all specified) formats to
        disk.

        :param formats: A set of formats to write. None = all configured

            e.g. {"html, "txt") etc. By default all formats will be stored.
        :param render: Defines if the pages shall be rendered (if necessary)
        :return: The VisualLog object
        """
        if formats is None:
            formats = self.log_formats

        if render:
            self.render(formats=formats)

        if self.log_to_disk:
            # store html
            if (
                self._html_export
                and self.html_filename is not None
                and len(self.html_filename) > 0
                and HTML in formats
            ):
                FileStag.save(self.html_filename, self.get_page(HTML))
                # store markdown
            if (
                self.md_export
                and self._md_filename is not None
                and len(self._md_filename) > 0
                and MD in formats
            ):
                FileStag.save(self._md_filename, self.get_page(MD))
            # store txt
            if (
                self.txt_export
                and self._txt_filename is not None
                and len(self._txt_filename) > 0
                and TXT in formats
            ):
                FileStag.save(self._txt_filename, self.get_page(TXT))
        return self

    def clear(self):
        """
        Clears the whole log (excluding headers and footers)
        """
        self.name_counter = Counter()
        self.title_counter = Counter()
        self._logs.clear()
        self.cur_element = self._logs

    def embed(self, log_data: PageSession):
        """
        Embeds another VisualLog's content into this one

        :param log_data: The source log page which shall be embedded
        """
        for cur_format in self.log_formats:
            if cur_format in log_data.log_formats:
                self.cur_element.add_data(cur_format, log_data.get_body(cur_format))

    def handle_modified(self):
        """
        Is called when a new block of content has been inserted
        """
        pass

    def reserve_unique_name(self, name: str, digits: int = 0):
        """
        Reserves a unique name within the log, e.g. to store an object to
        a unique file.

        :param name: The desired name
        :param digits: If provided the returned name will contain at least the given
            number of digits.
        :return: The effective name with which the data shall be stored
        """
        self.name_counter[name] += 1
        result = name
        if self.name_counter[name] > 1 or digits > 0:
            result += f"_{self.name_counter[name]:0{digits}d}"
        return result

    def begin_update(self) -> "PageUpdateContext":
        """
        Can be called at the beginning of a larger update block - e.g. if a page
        is completely cleared and re-built - to prevent page flickering.

        Will automatically created a backup of the page's previous state and will
        return this update until end_update is called as often as begin_update.

        A PageUpdateContext can be used via `with page_session.begin_update()` or in
        case of the builder `with builder.begin_update()` to automatically call
        end_update once the content block is left.
        """
        with self._page_lock, self._backup_lock:
            self._update_context_counter += 1
            if self._update_context_counter == 1:
                self.create_log_backup()
            from scistag.vislog.common.page_update_context import PageUpdateContext

            return PageUpdateContext(self)

    def end_update(self):
        """
        Ends the update mode
        """
        with self._backup_lock:
            self._update_context_counter -= 1

    def reset_client(self):
        """
        Is called when the client changed, e.g. because the page was reloaded
        """
        self.element_update_times = {}

    def get_events_js(self, client_id: str) -> [dict, bytes | None]:
        """
        Returns the newest events which need to be handled on client side
        (in JavaScript).

        :param client_id: The client's unique ID
        :return: Header data, Content data
        """
        with self._page_lock:
            if self._event_target_page is not None:
                return self._event_target_page.get_events_js(client_id)
        cur_time = time.time()
        refresh_time = 0.5
        if (
            self.next_event_time is not None
            and self.next_event_time - cur_time < refresh_time
        ):
            refresh_time = self.next_event_time - cur_time
            if refresh_time < self.minimum_refresh_time:
                refresh_time = self.minimum_refresh_time

        refresh_time_ms = int(round(refresh_time * 1000))  # convert refresh time to ms

        with self._page_lock:
            if self.last_client_id != client_id:  # page reloaded
                if client_id in self.old_client_ids:
                    return (
                        {
                            "action": "setContent",
                            "targetElement": ROOT_DOM_ELEMENT,
                            "vlRefreshTime": refresh_time_ms,
                        },
                        b"Session was opened in another browser or tab. "
                        b"Please close this one",
                    )
                self.reset_client()
                self.old_client_ids.add(client_id)
            self.last_client_id = client_id
            self.log.last_page_request = cur_time

            access_lock, root_element = self.get_root_element()
            with access_lock:
                element_list = root_element.list_elements_recursive()
                # ensure all elements are at least known
                for cur_element_ref in element_list:
                    if cur_element_ref.path not in self.element_update_times:
                        self.element_update_times[cur_element_ref.path] = 0.0
                modified_element_ref: LogElementReference | None = None
                change_time = 0.0
                for cur_element_ref in element_list:
                    if (
                        self.element_update_times[cur_element_ref.path]
                        < cur_element_ref.element.last_direct_change_time
                    ):
                        modified_element_ref = cur_element_ref
                        change_time = cur_element_ref.element.last_direct_change_time
                        break
                if modified_element_ref is None:
                    return {}, None
                path_start = modified_element_ref.path + "."
                for element_name in self.element_update_times.keys():
                    if (
                        element_name == modified_element_ref.path
                        or element_name.startswith(path_start)
                    ):
                        self.element_update_times[element_name] = change_time
                data = modified_element_ref.element.build(HTML)
                return {
                    "action": "setContent",
                    "targetElement": modified_element_ref.name,
                    "vlRefreshTime": refresh_time_ms,
                }, data

    def begin_sub_element(self, name: str) -> LogElement:
        """
        Begins a new sub element and sets it as writing target.

        Sub elements provide an easy way, e.g. via `with builder.cell()` to update
        individual regions of the log dynamically such as pages within pages.

        :param name: The unique name of the element to be added
        :return: The element which was created
        """
        new_element = self.cur_element.add_sub_element(name)
        self.element_stack.append(self.cur_element)
        self.cur_element = new_element
        return new_element

    def enter_element(self, element: LogElement):
        """
        Enters a previously created element to update it again

        :param element: The element to enter
        """
        self.element_stack.append(self.cur_element)
        self.cur_element = element

    def end_sub_element(self) -> LogElement:
        """
        Sets the previous LogElement as new target

        :return: The previous element which will become the new target now again
        """
        if len(self.element_stack) == 0:
            raise RuntimeError(
                "No remaining elements on target stack. Mismatching "
                "count of entering and leaving sub element regions."
            )
        self.cur_element = self.element_stack.pop()
        return self.cur_element

    def handle_events(self) -> float | None:
        """
        Handles the events

        :return: The timestamp at which we assume the next event to occur
        """
        with self._page_lock:
            if self._event_target_page is not None:
                self._event_target_page.handle_events()
        next_event: float | None = None
        next_event_time = self.builder.widget.handle_event_list()
        if next_event_time is not None:
            if next_event is None or next_event_time < next_event:
                next_event = next_event_time
        self.next_event_time = next_event_time
        return next_event

    def handle_client_event(self, **params):
        """
        Handles a client event (sent from JavaScript)

        :param params: The event parameters
        """
        with self._page_lock:
            if self._event_target_page is not None:
                self._event_target_page.handle_client_event(**params)
                return
        event_type = params.get("type", "")
        if event_type.startswith("widget_"):
            with self._page_lock:
                self.builder.widget.handle_client_event(**params)

    def _set_redirect_event_receiver(self, target_page: PageSession):
        with self._page_lock:
            self._event_target_page = target_page
