"""
Helper functions to export images of rendering methods for manual verification
"""
from __future__ import annotations

import base64
import hashlib
import html
import inspect
import io
import json
import os
import shutil
from collections import Counter
from typing import Any, Optional, TYPE_CHECKING

import filetype
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scistag.filestag import FileStag, FilePath
from scistag.imagestag import Image, Canvas, Size2D, Size2DTypes
from scistag.plotstag import Figure, Plot, MPHelper
from scistag.webstag import web_fetch
from .sub_log import SubLog, SubLogLock
from .. import LogLevel
from ..console_stag import Console

if TYPE_CHECKING:
    from .visual_log_renderer import VisualLogRenderer
    from .visual_log_renderer_html import VisualLogHtmlRenderer

HTML = "html"
"Html output"
CONSOLE = "console"
"Console output"
TXT = "txt"
"Txt output"
MD = "md"
"Markdown output"

MAIN_LOG = "mainLog"
"The name of the main log"

if TYPE_CHECKING:
    from scistag.imagestag.pixel_format import PixelFormat


class VisualLog:
    """
    Helper class which logs visual results to the disk for verification and
    helps to assert their consistency.
    """

    def __init__(self, target_dir: str,
                 title: str,
                 formats_out: set[str] = {"html"},
                 ref_dir: str | None = None,
                 tmp_dir: str | None = None,
                 clear_target_dir: bool = False,
                 log_to_disk=True,
                 embed_images: bool | None = None,
                 continuous_write=False,
                 refresh_time_s=0.5,
                 max_fig_size: Size2DTypes | None = None):
        """
        Begins a test with visual outputs

        :param target_dir: The output directory
        :param title: The log's name
        :param formats_out: A set of the formats to export.
            "html", "txt" (pure Text)  and "md" (markdown) are supported.
        :param ref_dir: The directory in which the reference data objects
            can be stored.
        :param tmp_dir: A directory in which temporary files can be stored.
            Will be deleted upon finalization.
        :param clear_target_dir: Defines if the target dir shall be deleted
            before starting (take care!)
        :param log_name: The title of the log
        :param log_to_disk: Defines if the logger shall write it's results
            to disk
        :param embed_images: Defines if images shall be directly embedded into
            the HTML log instead of being stored as separate files.
            By default True if Markdown is not set as one of the "formats_out",
            otherwise False by default as Markdown will need the files on disk.
        :param continuous_write: Defines if the log shall be written to disk
            after every added element. False by default.
        :param refresh_time_s: The time interval in seconds in which the
            auto-reloader html page (liveView.html) tries to refresh the page.
            The lower the time the more often the page is refreshed.
        :param max_fig_size: The optimum, maximum width and height for
            embedded figures and images
        """
        try:
            if clear_target_dir:
                shutil.rmtree(target_dir)
        except FileNotFoundError:
            pass
        self.ref_dir = FilePath.norm_path(
            target_dir + "/ref" if ref_dir is None else ref_dir)
        "The directory in which reference files for comparison shall be stored"
        self.tmp_path = FilePath.norm_path(
            target_dir + "/temp" if tmp_dir is None else tmp_dir)
        "Output directory for temporary files"
        os.makedirs(self.tmp_path, exist_ok=True)
        os.makedirs(self.ref_dir, exist_ok=True)
        self.target_dir = target_dir
        "The directory in which the logs shall be stored"
        os.makedirs(self.target_dir, exist_ok=True)
        self._log_to_disk = log_to_disk
        "Defines if the images and the html data shall be written to disk"
        self._log_images = True
        "Defines if images shall be logged to disk"
        self.name_counter = Counter()
        "Counter for file names to prevent writing to the same file twice"
        self.title_counter = Counter()
        "Counter for titles to numerate the if appearing twice"
        self.refresh_time_s = refresh_time_s
        self._provide_live_view()
        """
        The time interval with which the log shall be refreshed when using
        the liveViewer (see Live_view)
        """
        if max_fig_size is not None and not isinstance(max_fig_size, Size2D):
            max_fig_size = Size2D(max_fig_size)
        else:
            max_fig_size = Size2D(1024, 1024)
        "Defines the preview's width and height"
        self._log_formats = formats_out
        "Defines if text shall be logged"
        self._log_formats.add(CONSOLE)
        self._log_stag: list[SubLog] = []
        """
        A stag for temporary switching log targets and to created 'nested"
        logs.
        """
        self.sub_log_data: dict[str, dict[str, bytes]] = {}
        """
        Contains the content of each "sub log", see :meth:`begin_sub_log`.
        """
        self._logs: dict[str, list[bytes]] = {element: [] for element in
                                              sorted(self._log_formats)}
        self._log_stag.append(SubLog(logs=self._logs, target="",
                                     max_fig_size=max_fig_size.to_int_tuple()))
        """
        Contains the log data for each output type
        """
        self.continuous_write = continuous_write
        "If defined the output logs will be updated after every log"
        self.markdown_html = True
        "Defines if markdown shall support html embedding"
        self._log_txt_images = True
        "Defines if images shall also be logged to text files as ASCII"
        self._use_tabulate = True
        "Defines if tabulate may be used"
        self._use_pretty_html_table = True
        "Defines if pretty html shall be used"
        self._html_table_style = 'blue_light'
        "The pretty html style to be used"
        self._txt_table_format = "rounded_outline"
        "The text table format to use in tabulate"
        self._md_table_format = "github"
        "The markdown table format to use"
        self._embed_images = embed_images if embed_images is not None else \
            not MD in formats_out
        "If defined images will be embedded directly into the HTML code"
        self._image_default_format = "png"
        "The default image type to use for storage"
        self._html_export = HTML in self._log_formats
        "Defines if HTML gets exported"
        self._md_export = MD in self._log_formats
        "Defines if markdown gets exported"
        self._txt_export = TXT in self._log_formats
        "Defines if txt gets exported"
        self._txt_filename = self.target_dir + "/index.txt"
        "The name of the txt file to which we shall save"
        self._html_filename = self.target_dir + "/index.html"
        "The name of the html file to which we shall save"
        self._md_filename = self.target_dir + "/index.md"
        "The name of the markdown file to which we shall save"
        self._consoles: list[Console] = []
        "Attached consoles to which the data shall be logged"
        self._log_limit = -1
        """
        The current log limit (maximum number of rows before starting deleting 
        the oldest ones)
        """
        from .visual_log_renderer_html import VisualLogHtmlRenderer
        self._renderers: dict[str, "VisualLogRenderer"] = {
            HTML: VisualLogHtmlRenderer()}
        "The renderers for the single supported formats"
        self.forward_targets: dict[str, VisualLog] = {}
        "List of logs to which all rendering commands shall be forwarded"

    def set_log_limit(self, limit: int):
        """
        Changes the maximum count of log rows for the current sub log.

        If the number gets exceeded it will automatically start deleting the
        oldest logs.

        :param limit: The new limit. -1 = None
        """
        self._log_stag[-1].log_limit = limit
        self._log_limit = limit

    def add_console(self, console: Console):
        """
        Adds an advanced console as target to the log

        :param console: The console to add
        """
        self._consoles.append(console)

    @staticmethod
    def _get_module_path() -> str:
        """
        Returns the path of the VisualStag module

        :return: The path
        """
        return FilePath.dirname(__file__)

    def clear_logs(self):
        """
        Clears the whole log (excluding headers and footers)
        """
        for key in self._logs.keys():
            self._logs[key].clear()

    @property
    def max_fig_size(self) -> Size2D:
        """
        The maximum figure size in pixels
        """
        return Size2D(self._log_stag[-1].max_fig_size)

    def clip_logs(self):
        """
        Checks if the log limited exceeded and clips old logs if necessary.
        """
        if self._log_limit != -1:
            for key, elements in self._logs.items():
                exc_elements = len(elements) - self._log_limit
                if exc_elements > 0:
                    self._logs[key] = elements[exc_elements:]

    def begin_sub_log(self, target: str,
                      max_fig_size: Size2DTypes | None = None) -> SubLogLock:
        """
        Pushes the current log target to create a sub log.

        You can call this method for the same target multiple
        times so the logs get attached to each other.
        When ever :meth:`end_sub_log` is called self.sub_log_data is updated
        with all elements on the stack which participate towards the
        same target. These can then (for example) be used to combine them
        to a custom html or txt log via customizing the `get_body` function.

        Usage:

        ..  code-block: Python

            with v.begin_sub_log():
                ...

        :param target: The sub log's name in which the content shall be stored.
            See :attr:`sub_log_data`.
        :param max_fig_size: Defines the maximum size of visual elements
        """
        if len(self._log_stag) > 100:
            raise AssertionError("Maximum log stag depth exceeded, something "
                                 "is likely wrong and you did not cleanly "
                                 "leave the current update's section.")
        new_logs = {}
        for key, value in self._logs.items():
            new_logs[key] = []

        if max_fig_size is not None:
            if not isinstance(max_fig_size, Size2D):
                max_fig_size = Size2D(max_fig_size)
        else:
            max_fig_size = self._log_stag[0].max_fig_size

        self._log_stag.append(SubLog(logs=new_logs, target=target,
                                     max_fig_size=max_fig_size.to_int_tuple()))
        self._logs = new_logs
        return SubLogLock(self)

    def end_sub_log(self):
        """
        Ends a sub log, aggregates all logs which participated to the
        current target and stores the content in sub_log_data[target] which
        can then be used to customize def get_body()
        """
        if len(self._log_stag) == 0:
            raise AssertionError("Tried to decrease log stag without remaining "
                                 "elements")
        top_target = self._log_stag[-1].target
        target_data = {}
        # initialize empty data streams for each target type (md, html etc.)
        for key, value in self._logs.items():
            target_data[key] = b""
        for element in self._log_stag:  # for all logs on the stag
            if element.target == top_target:  # if it matches our target type
                cur_logs = element.logs
                # for all target types of this log
                for target_type, target_log_list in cur_logs.items():
                    new_data = b"".join(target_log_list)
                    if len(new_data) >= 1:
                        pass
                    target_data[target_type] += new_data
        self.sub_log_data[top_target] = target_data
        self._log_stag.pop()
        self._logs = self._log_stag[-1].logs  # restore previous log target
        self._log_limit = self._log_stag[-1].log_limit  # restore log limi

    def _need_images_on_disk(self) -> bool:
        """
        Returns if images NEED to be stored on disk

        :return: True if they do
        """
        return self._md_export or not self._embed_images

    def _provide_live_view(self):
        """
        Assembles a website file which automatically updates the
        logged html file as often as possible when ever it is updated
        on disk.
        """
        base_path = self._get_module_path()
        FileStag.copy(base_path + "/css/visual_log.css",
                      f"{self.target_dir}/css/visual_log.css",
                      create_dir=True)
        import jinja2
        environment = jinja2.Environment()
        template = environment.from_string(
            FileStag.load_text_file(base_path + "/templates/liveView.html"))
        rendered_lv = template.render(title="VisualLiveLog Viewer",
                                      reload_timeout=2000,
                                      retry_frequency=100,
                                      reload_frequency=int(
                                          self.refresh_time_s * 1000),
                                      reload_url="index.html")
        FileStag.save_text_file(self.target_dir + "/liveView.html",
                                rendered_lv)

    def image(self, name: str,
              source: Image | Canvas | str | bytes | np.ndarray,
              alt_text: str | None = None,
              pixel_format: Optional["PixelFormat"] | str | None = None,
              download: bool = False,
              scaling: float = 1.0):
        """
        Writes the image to disk for manual verification

        :param name: The name of the test.
            Will result in a file named logs/TEST_DIR/test_name.png
        :param source: The data object
        :param alt_text: An alternative text if no image can be displayed
        :param pixel_format: The pixel format (in case the image is passed
            as numpy array). By default gray will be used for single channel,
            RGB for triple band and RGBA for quad band sources.
        :param download: Defines if an image shall be downloaded
        :param scaling: The factor by which the image shall be scaled
        """
        if not self._log_images:
            return
        if alt_text is None:
            alt_text = name
        if self._log_txt_images:
            download = True
        if isinstance(source, np.ndarray):
            source = Image(source, pixel_format=pixel_format)
        if isinstance(source, str):
            if not source.lower().startswith("http") or download or \
                    self._embed_images:
                source = web_fetch(source, cache=True)
            else:
                self._insert_image_reference(name, source, alt_text, scaling)
                return
        self.name_counter[name] += 1
        filename = name
        if self.name_counter[name] > 1:
            filename += f"__{self.name_counter[name]}"
        if isinstance(source, Canvas):
            source = source.to_image()
        if scaling != 1.0:
            if not isinstance(source, Image):
                source = Image(source).resized_ext(factor=scaling)
            else:
                source = source.resized_ext(factor=scaling)
        if self._log_to_disk:
            self._log_image_to_disk(filename, name, source)
        if self._log_txt_images and (self._txt_export or len(self._consoles)):
            if not isinstance(source, Image):
                source = Image(source)
            max_width = min(max(source.width / 1024 * 80, 1), 80)
            self._add_txt(source.to_ascii(max_width=max_width))
            self._add_txt(f"Image: {alt_text}\n")
        else:
            self._add_txt(f"\n[IMAGE][{alt_text}]\n")
        self.clip_logs()

    def _insert_image_reference(self, name, source, alt_text, scaling):
        """
        Inserts a link to an image in the html logger without actually
        downloading or storing the image locally

        :param name: The image's name
        :param source: The url
        :param alt_text: The alternative display text
        :param scaling: The scaling factor
        :return:
        """
        if scaling != 1.0:
            image = Image(source)
            width, height = (int(round(image.width * scaling)),
                             int(round(image.height * scaling)))
            self._add_html(
                f'<img src="{source}" with={width} height={height}>'
                f'<br>')
        else:
            self._add_html(f'<img src="{source}"><br>')
        self._add_md(f'![{name}]({source})\n')
        self._add_txt(f"\n[IMAGE][{alt_text}]\n")
        self.clip_logs()

    def _log_image_to_disk(self, filename, name, source):
        """
        Stores an image on the disk

        :param filename:  The output filename
        :param name:  The image's name
        :param source: The data source
        """
        if isinstance(source, bytes):
            import filetype
            file_type = filetype.guess(source)
            target_filename = self.target_dir + \
                              f"/{filename}.{file_type.extension}"
            encoded_image = source
            if self._need_images_on_disk():
                FileStag.save_file(target_filename, source)
        else:
            target_filename = \
                self.target_dir + f"/{filename}.{self._image_default_format}"
            encoded_image = source.encode(
                filetype=self._image_default_format)
            if self._need_images_on_disk():
                FileStag.save_file(target_filename, encoded_image)
        if self._embed_images:
            embed_data = self._build_get_embedded_image(encoded_image)
            self._add_html(
                f'<img src="{embed_data}"><br>')
        else:
            self._add_html(
                f'<img src="{os.path.basename(target_filename)}"><br>')
        if self._md_export:
            self._add_md(
                f'![{name}]({os.path.basename(target_filename)})\n')
        self.clip_logs()

    @staticmethod
    def _build_get_embedded_image(source: bytes) -> str:
        """
        Encodes an image to ASCII to embed it directly into an HTML page

        :param source: The source data
        :return: The string to embed
        """
        ft = filetype.guess(source)
        mime_type = ft.mime
        base64_data = base64.encodebytes(source).decode("ASCII")
        return f"data:{mime_type};base64,{base64_data}"

    def evaluate(self, code: str, log_code: bool = True) -> Any:
        """
        Runs a piece of code and returns it's output

        :param code: The code to execute
        :param log_code: Defines if the code shall be added to the log
        :return: The returned data (if any)
        """
        frame = inspect.currentframe()
        result = eval(code, frame.f_back.f_globals, frame.f_back.f_locals)
        if log_code:
            if result is not None:
                self.code(code + f"\n>>> {result}")
            else:
                self.code(code)
        return result

    def title(self, text: str):
        """
        Adds a title to the log

        :param text: The title's text
        :return:
        """
        self.sub(text, level=1)

    def text(self, text: str):
        """
        Adds a text to the log

        :param text: The text to add to the log
        :return:
        """
        for element in self.forward_targets.values():
            element.text(text)
        lines = html.escape(text)
        lines = lines.split("\n")
        for index, text in enumerate(lines):
            self._add_html(f'{text}<br>')
            if index == len(lines) - 1:
                self._add_md(f"{text}")
            else:
                self._add_md(f"{text}\\")
            self._add_txt(text)
        self.clip_logs()

    def sub(self, text: str, level: int = 2):
        """
        Adds a sub title to the log

        :param text: The text to add to the log
        :param level: The title level (0..5)
        :return:
        """
        assert 0 <= level <= 5
        for element in self.forward_targets.values():
            element.sub(text)
        md_level = "#" * level
        escaped_lines = html.escape(text)
        for cur_row in escaped_lines.split("\n"):
            self._add_html(f'<h{level}>{cur_row}</h{level}>')
        self._add_md(f"{md_level} {text}")
        if self._add_txt(text) and level <= 4:
            character = "=" if level < 2 else "-"
            self._add_txt(character * len(text))
        self._add_txt("")
        self.clip_logs()

    def sub_x3(self, text: str):
        """
        Adds a sub title to the log

        :param text: The text to add to the log
        :return:
        """
        self.sub(text, level=3)

    def sub_x4(self, text: str):
        """
        Adds a sub title to the log

        :param text: The text to add to the log
        :return:
        """
        self.sub(text, level=4)

    def test(self, text: str):
        """
        Adds a test section to the log

        :param text: The text to add to the log
        :return:
        """
        self.sub(text, level=1)

    def sub_test(self, text: str):
        """
        Adds a sub test section to the log

        :param text: The text to add to the log
        :return:
        """
        self.sub(text, level=4)

    def md(self, text: str):
        """
        Adds a markdown section.

        Requires the Markdown package to be installed.

        :param text: The text to parse
        """
        for element in self.forward_targets.values():
            element.md(text)
        import markdown
        parsed = markdown.markdown(text)
        self._add_md(text + "\n")
        self._add_html(parsed)
        self._add_txt(text)
        self.clip_logs()

    def html(self, code: str):
        """
        Adds a html section. (only to targets supporting html)

        :param code: The html code to parse
        """
        for element in self.forward_targets.values():
            element.html(code)
        self._add_md(code)
        self._add_html(code)
        self.clip_logs()

    def code(self, code: str):
        """
        Adds code to the log
        :param code: The code to execute
        """
        for element in self.forward_targets.values():
            element.code(code)
        escaped_code = html.escape(code).replace("\n", "<br>")
        self._add_html(f'Code<br><table class="source_code">'
                       f'<tr><td style="padding: 5px;" align="left">'
                       f'<code>{escaped_code}</code>'
                       f'</td></tr></table><br><br>')
        self._add_md(f"```\n{code}\n```")
        self._add_txt(code)
        self.clip_logs()

    @staticmethod
    def _encode_html(text: str) -> str:
        """
        Escaped text to html compatible text

        :param text: The original unicode text
        :return: The escaped text
        """
        escaped = html.escape(text)
        res = escaped.encode('ascii', 'xmlcharrefreplace')
        return res.decode("utf-8")

    def log(self, text: Any, level: LogLevel = LogLevel.INFO):
        """
        Adds a log text to the log

        :param text: The text to add to the log
        :param level: The importance / category of the log entry
        :return:
        """
        if text is None:
            text = "None"
        if not isinstance(text, str):
            text = str(text)
        for element in self.forward_targets.values():
            element.log(text, level=level)
        escaped_text = self._encode_html(text)
        self._add_html(
            f'<p class="logtext">{self._html_linebreaks(escaped_text)}</p><br>')
        if MD in self._logs and len(self._logs[MD]) > 0:
            last_md_log: str = self._logs[MD][-1].decode("utf-8")
            if last_md_log.endswith("```\n"):
                self._add_md(f"{text}\n```")
        else:
            self._add_md(f"```\n{text}\n```")
        self._add_txt(text)
        self.clip_logs()

    def df(self, name: str, df: pd.DataFrame, index: bool = True):
        """
        Adds a dataframe to the log

        :param name: The dataframe's name
        :param df: The data frame
        :param index: Defines if the index shall be printed
        """
        for element in self.forward_targets.values():
            element.df(name=name, df=df, index=index)
        if self._use_pretty_html_table:
            try:
                import pretty_html_table
                html_code = pretty_html_table.build_table(df,
                                                          self._html_table_style,
                                                          index=True)
            except ModuleNotFoundError:  # pragma: no-cover
                html_code = df.to_html(index=index)
        else:
            html_code = df.to_html(index=index)
        self._add_html(html_code)
        if self._use_tabulate:
            try:
                import tabulate
                md_table = df.to_markdown(index=index,
                                          tablefmt=self._md_table_format)
                self._add_md(md_table)
                self._add_txt(
                    df.to_markdown(index=index,
                                   tablefmt=self._txt_table_format) + "\n")
                return
            except ModuleNotFoundError:  # pragma: no-cover
                pass
        else:
            string_table = df.to_string(index=index) + "\n"
            if self.markdown_html:
                self._add_md(html_code)
            else:
                self._add_md(string_table)
            self._add_txt(string_table)
        self.clip_logs()

    def figure(self, name: str, figure: plt.Figure | plt.Axes | Figure | Plot,
               alt_text: str | None = None,
               _out_image_data: io.IOBase | None = None):
        """
        Adds a figure to the log

        :param name: The figure's name
        :param figure: The figure to log
        :param alt_text: An alternative text to display if the figure can
            not be displayed.
        :param _out_image_data: Receives the image data if provided (for
            debugging and assertion purposes)
        """
        if not self._log_images and _out_image_data is None:
            return
        if isinstance(figure, (Figure, Plot)):
            image = figure.render()
            self.image(name, image, alt_text=alt_text)
            if _out_image_data is not None:
                _out_image_data.write(image.encode(filetype="png"))
            return
        if not isinstance(figure, plt.Figure):
            figure = figure.figure
        image_data = MPHelper.figure_to_png(figure, transparent=False)
        if _out_image_data is not None:
            _out_image_data.write(image_data)
        self.image(name, image_data, alt_text=alt_text)

    def log_dict(self, dict_or_list: dict | list):
        """
        Logs a dictionary or a list.

        The data needs to be JSON compatible so can contain further nested
        diotionaries, lists, floats, booleans or integers but no more
        complex types.

        :param dict_or_list: The dictionary or list
        """
        from scistag.common.dict import dict_to_bullet_list
        dict_tree = dict_to_bullet_list(dict_or_list, level=0, bold=True)
        self.md(dict_tree)

    def log_list(self, list_data: list):
        """
        Logs a list (just for convenience), forwards to log_dict.

        The data needs to be JSON compatible so can contain further nested
        diotionaries, lists, floats, booleans or integers but no more
        complex types.

        :param list_data: The list to log
        """
        self.log_dict(list_data)

    def hash_check_log(self, value, assumed):
        """
        Verifies a hash and adds the outcome of a hash check to the output

        :param value: The hash value
        :param assumed: The assumed value
        """
        if value != assumed:
            self.log(
                f"⚠️Hash validation failed!\nValue:  {value}\nAssumed: {assumed}")
            self.write_to_disk()
            raise AssertionError("Hash mismatch - "
                                 f"Found: {value} - "
                                 f"Assumed: {assumed}")
        else:
            self.log(f"{assumed} ✔")

    def assert_figure(self, name: str,
                      figure: plt.Figure | plt.Axes | Figure | Plot,
                      hash_val: str,
                      alt_text: str | None = None):
        """
        Adds a figure to the log and verifies it's content to a checksum

        :param name: The figure's name
        :param figure: The figure to log
        :param alt_text: An alternative text to display if the figure can
            not be displayed.
        :param hash_val: The hash value to compare to (a checksum of all
            pixels). The correct will be logged via an assertion upon failure
            and can then be copies & pasted.
        """
        image_data = io.BytesIO()
        self.figure(name, figure=figure, alt_text=alt_text,
                    _out_image_data=image_data)
        assert len(image_data.getvalue()) > 0
        result_hash_val = hashlib.md5(image_data.getvalue()).hexdigest()
        self.hash_check_log(result_hash_val, hash_val)

    def assert_image(self, name: str, source: Image | Canvas, hash_val: str,
                     scaling: float = 1.0,
                     alt_text: str | None = None):
        """
        Assert an image object and verifies it's hash value matches the object's
        hash.

        :param name: The name of the object
        :param source: The data to log
        :param hash_val: The hash value to compare to (a checksum of all
            pixels). The correct will be logged via an assertion upon failure
            and can then be copies & pasted.
        :param scaling: The factor by which the image shall be scaled
        :param alt_text: An alternative text to display if the image can
            not be displayed.
        """
        result_hash_val = self.log_and_hash_image(name=name,
                                                  data=source,
                                                  scaling=scaling,
                                                  alt_text=alt_text)
        self.hash_check_log(result_hash_val, hash_val)

    def log_and_hash_image(self, name: str,
                           data: Image | Canvas,
                           alt_text: str | None = None,
                           scaling: float = 1.0) -> str:
        """
        Writes the image to disk for manual verification (if enabled in the
        test_config) and returns it's hash.

        :param name: The name of the test.
            Will result in a file named logs/TEST_DIR/test_name.png
        :param data: The image object
        :param alt_text: An alternative text to display if the image can
            not be displayed.
        :param scaling: The factor by which the image shall be scaled
        :return: The image's hash for consistency checks
        """
        if isinstance(data, Canvas):
            data = data.to_image()
        self.image(name=name, source=data, alt_text=alt_text, scaling=scaling)
        return data.get_hash()

    def assert_text(self, name: str, text: str, hash_val: str):
        """
        Asserts a text for validity and logs it

        :param name: The assertion's name
        :param text: The text data
        :param hash_val: The assumed hash value
        """
        result_hash_val = hashlib.md5(text.encode("utf-8")).hexdigest()
        self.text(text)
        self.hash_check_log(result_hash_val, hash_val)

    def assert_df(self, name: str,
                  df: pd.DataFrame,
                  dump: bool = False,
                  hash_val: str | None = None):
        """
        Asserts the integrity of a dataframe

        :param name: The name
        :param df: The data frame's part to verify
        :param dump: Defines if the data fram shall be dumped to disk.
            To this once for a new data frame to create a reference
        :param hash_val: If specified the dataframe will get dumped as csv
            of which the hash value is compared to the one passed.
        """
        if hash_val is not None:
            output = io.BytesIO()
            df.to_csv(output)
            result_hash_val = hashlib.md5(output.getvalue()).hexdigest()
            if result_hash_val != hash_val:
                self.write_to_disk()
                raise AssertionError("Hash mismatch - "
                                     f"Found: {result_hash_val} - "
                                     f"Assumed: {hash_val}")
            return
        if dump:
            output = io.BytesIO()
            df.to_parquet(output, engine='pyarrow')
            self.save_ref(name, output.getvalue())
            print(f"Warning - Updating test reference of {name}")
        comp_data = self.load_ref(name)
        if comp_data is None:
            raise AssertionError(f"No reference data provided for {name}")
        comp_df = pd.read_parquet(io.BytesIO(comp_data), engine='pyarrow')
        if not comp_df.equals(df):
            raise AssertionError(
                f"Data mismatch between {name} and it's reference")

    def assert_np(self, name: str,
                  data: np.ndarray,
                  variance_abs: float | None = None,
                  dump: bool = False,
                  rounded: int = None,
                  hash_val: bool | None = None):
        """
        Asserts a nunpy array for validity and logs it

        :param name: The assertion's name
        :param data: The data
        :param variance_abs: The maximum, absolute variance to the original,
            0.0 by default.
        :param dump: Defines if the current dump shall be overwritten.
            Set this once to true when you on purpose changed the data and
             verified it.
        :param rounded: Pass this if you want to hash floating point
            arrays where a rounded integer precision is enough.

            rounded defines how many digits behind the comma are relevant,
            so 0 rounds to full ints, +1 rounds to 0.1, +2 rounds to 0.01
            etc. pp.
        :param hash_val: The hash value to use as orientation.

            Do not use this for floating point data types due to
            platform dependent (slight) data discrepancies.
        """
        if rounded is not None:
            data = (data * (10 ** rounded)).astype(int)
        if hash_val is not None:
            if data.dtype == float:
                raise NotImplementedError("Hashing not supported for float"
                                          "matrices")
            result_hash_val = hashlib.md5(data.tobytes()).hexdigest()
            if result_hash_val != hash_val:
                self.write_to_disk()
                raise AssertionError("Hash mismatch - "
                                     f"Found: {result_hash_val} - "
                                     f"Assumed: {hash_val}")
            return
        if dump:
            output = io.BytesIO()
            np.save(output, data)
            self.save_ref(name, output.getvalue())
            print(f"Warning - Updating test reference of {name}")
        comp_data = self.load_ref(name)
        if comp_data is None:
            raise AssertionError(f"No reference data provided for {name}")
        np_array = np.load(io.BytesIO(comp_data))
        if variance_abs == 0.0 or variance_abs is None:
            if np.all(np_array == data):
                return
        else:
            if np.all(np.abs(np_array - data) <= variance_abs):
                return
        raise AssertionError(f"Data mismatch between {name} and it's reference")

    def assert_val(self, name: str,
                   data: dict | list | str | Image | Figure | pd.DataFrame,
                   hash_val: str | None = None):
        """
        Asserts a text for validity and logs it

        :param name: The assertion's name
        :param data: The data
        :param hash_val: The assumed hash value (not required for data w/
            reference)
        """
        # image
        if isinstance(data, Image):
            self.assert_image(name, data, hash_val=hash_val)
            return
        # figure
        if isinstance(data, Figure):
            self.assert_figure(name, data, hash_val=hash_val)
            return
        # pandas data frame
        if isinstance(data, pd.DataFrame):
            self.assert_df(name, data)
            return
        # numpy array
        if isinstance(data, np.ndarray):
            self.assert_np(name, data, hash_val=hash_val)
            return
        if isinstance(data, str):
            self.assert_text(name, data, hash_val=hash_val)
            return
            # dict or list
        if isinstance(data, (list, dict, str)):
            self.log(str(data))  # no beautiful logging supported yet
            data = json.dumps(data).encode("utf-8")
        if data is None or not isinstance(data, bytes):
            raise NotImplementedError("Data type not supported")
        result_hash_val = hashlib.md5(data).hexdigest()
        self.hash_check_log(result_hash_val, hash_val)

    def save_ref(self, name: str, data: bytes):
        """
        Saves a new data reference

        :param name: The reference's unique name
        :param data: The data to store
        """
        hashed_name = self._get_hashed_filename(name)
        hash_fn = self.ref_dir + "/" + hashed_name + ".dmp"
        FileStag.save_file(hash_fn, data)

    def load_ref(self, name: str) -> bytes | None:
        """
        Loads the data reference

        :param name: The reference's unique name
        :return: The data. None if no reference could be found
        """
        hashed_name = self._get_hashed_filename(name)
        hash_fn = self.ref_dir + "/" + hashed_name + ".dmp"
        if FileStag.exists(hash_fn):
            return FileStag.load_file(hash_fn)
        return None

    def _get_hashed_filename(self, name):
        """
        Returns a hashed filename for name to be store it with a fixed size
        on disk

        :param name: The file's name
        :return: The hash name to be used as filename
        """
        hashed_name = hashlib.md5(name.encode('utf-8')).hexdigest()
        return hashed_name

    def _html_linebreaks(self, text: str) -> str:
        """
        Replaces linebreaks through html linebreaks

        :param text: The original text
        :return: The text with html linebreaks
        """
        return text.replace("\n\r", "\n").replace("\n", "<br>")

    def _add_html(self, html_code: str):
        """
        The HTML code to add

        :param html_code: The html code
        :return: True if txt logging is enabled
        """
        if HTML not in self._logs:
            return
        self._logs[HTML].append(html_code.encode("utf-8"))
        if self.continuous_write:
            self.write_to_disk(formats={HTML})
        return True

    def _add_md(self, md_code: str, no_break: bool = False):
        """
        The markdown code to add

        :param md_code: The markdown code
        :param no_break: If defined no line break will be added
        :return: True if txt logging is enabled
        """
        if MD not in self._logs:
            return
        new_text = md_code + ("" if no_break else "\n")
        self._logs[MD].append(new_text.encode("utf-8"))
        if self.continuous_write:
            self.write_to_disk(formats={MD})
        return True

    def _add_txt(self, txt_code: str, console: bool = True):
        """
        Adds text code to the txt / console log

        :param txt_code: The text to add
        :param console: Defines if the text shall also be added ot the
            console's log (as it's mostly identical). True by default.
        :return: True if txt logging is enabled
        """
        if TXT not in self._logs:
            return
        self._logs[TXT].append((txt_code + "\n").encode("utf-8"))
        if console and len(self._consoles):
            self._add_to_console(txt_code)
        if self.continuous_write:
            self.write_to_disk(formats={TXT})
        return True

    def _add_to_console(self, txt_code: str):
        """
        Adds text code to the console log

        :param txt_code: The text to add
        :return: True if txt logging is enabled
        """
        for console in self._consoles:
            if console.progressive and len(self._log_stag) == 1:
                console.print(txt_code)
        self._logs[CONSOLE].append((txt_code + "\n").encode("ascii"))
        return True

    def get_temp_path(self, relative: str | None = None) -> str:
        """
        Returns the temporary file path. The data will be wiped upon the call
        of finalize.

        :param relative: A relative path which can be passed and automatically
            gets concatenated.
        :return: The path or combined path
        """
        if relative is not None:
            return FilePath.norm_path(self.tmp_path + "/" + relative)
        return self.tmp_path

    def _build_body(self, base_log: dict[str:bytes]):
        """
        Requests to combine all logs and sub logs to a single page which
        can be logged to the disk or provided in the browser. (excluding
        html headers and footers), so just "the body" of the HTML page.

        :param base_log: The byte stream of all concatenated logs for each
            output type.
        :return: The finalized page, e.g. by combining base_log w/
            sub_logs as shown in the :class:`VisualLiveLog` class.
        """
        body: dict[str, bytes] = {}
        for cur_format, log_entries in base_log.items():
            body[cur_format] = b"".join(log_entries)

        for cur_format in self._log_formats:
            sub_log_data = {MAIN_LOG: b"".join(self._logs[cur_format])}
            for sl_key, sl_data in self.sub_log_data.items():
                if cur_format in sl_data:
                    sub_log_data[sl_key] = sl_data[cur_format]

            if cur_format == HTML:
                body[cur_format] = \
                    self._renderers[HTML].build_body(
                        sub_log_data)
        return body

    def flush(self):
        """
        Writes the current state to disk
        """
        self.write_to_disk()

    def write_to_disk(self, formats: set[str] | None = None):
        """
        Finalizes the log and summarizes the result in an index.html file
        in the specified target directory.

        :param formats: A set of formats to write. None = all configured
        """
        if formats is None:
            formats = self._log_formats
        bodies = self._build_body(self._logs)
        if self._log_to_disk:
            # store html
            if self._html_export and self._html_filename is not None and \
                    len(self._html_filename) > 0 and HTML in formats:
                full_page = self._renderers[HTML].build_page(bodies[HTML])
                FileStag.save_file(self._html_filename, full_page)
            # store markdown
            if self._md_export and self._md_filename is not None and \
                    len(self._md_filename) > 0 and MD in formats:
                body = bodies[MD]
                FileStag.save_file(self._md_filename, body)
            # store txt
            if self._txt_export and self._txt_filename is not None and \
                    len(self._txt_filename) > 0 and TXT in formats:
                body = bodies[TXT]
                FileStag.save_file(self._txt_filename, body)
        if CONSOLE in formats:
            for console in self._consoles:
                if console.progressive:
                    continue
                console.clear()
                body = bodies[CONSOLE]
                console.print(body.decode("ascii"))

    def finalize(self):
        """
        Finalizes the report and writes it to disk
        """
        self.write_to_disk()
        if FilePath.exists(self.tmp_path):
            shutil.rmtree(self.tmp_path)
