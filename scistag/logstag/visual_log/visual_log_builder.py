from __future__ import annotations

import time
from collections import Counter
from typing import Optional, Any, TYPE_CHECKING
import io

import base64
import html

import hashlib

import numpy as np
import pandas as pd
from filetype import filetype
from matplotlib import pyplot as plt

from scistag.filestag import FileStag, FilePath
from scistag.imagestag import Image, Canvas, PixelFormat, Size2D
from scistag.logstag import LogLevel

from scistag.logstag.visual_log.visual_log import VisualLog, MD, TXT, HTML, \
    TABLE_PIPE
from scistag.plotstag import Figure, Plot, MPHelper

if TYPE_CHECKING:
    from scistag.logstag.visual_log.pyplot_log_context import PyPlotLogContext


class VisualLogBuilder:
    """
    Defines an interface to all major log writing and creation functions
    for the creation of a VisualLog.

    Can be overwritten to be provided as callback target for dynamic
    documentation creation.
    """

    def __init__(self):
        self._log: "VisualLog" = None
        "The main logging target"
        self.logs = self._log.logs
        self.log_formats = self._log.log_formats
        self.log_images = self._log.log_images
        self.log_to_disk = self._log.log_to_disk
        self.log_txt_images = self._log.log_txt_images
        self.ref_dir = self._log.ref_dir
        self.markdown_html = self._log.markdown_html
        self.embed_images = self._log.embed_images
        self.md_export = self._log.md_export
        self.txt_export = self._log.txt_export
        self.image_format = self._log.image_format
        self.image_quality = self._log.image_quality
        self.target_dir = self._log.target_dir
        self.forward_targets: dict[str, VisualLogBuilder] = {}
        "List of logs to which all rendering commands shall be forwarded"
        self.name_counter = Counter()
        "Counter for file names to prevent writing to the same file twice"
        self.title_counter = Counter()
        "Counter for titles to numerate the if appearing twice"
        self._total_update_counter = 0
        "The total number of updates to this log"
        self._update_counter = 0
        # The amount of updates since the last statistics update
        self._last_statistic_update = time.time()
        "THe last time the _update rate was computed as time stamp"
        self._update_rate: float = 0
        # The last computed updated rate in updates per second

    @property
    def max_fig_size(self) -> Size2D:
        """
        The maximum figure size in pixels
        """
        return self._log.max_fig_size

    def clear(self):
        """
        Clears the whole log (excluding headers and footers)
        """
        self.name_counter = Counter()
        self.title_counter = Counter()
        for key in self.logs.keys():
            self.logs[key].clear()

    def embed(self, log: VisualLog):
        """
        Embeds another VisualLog's content into this one

        :param log: The source log
        """
        for cur_format in self.log_formats:
            if cur_format in log.log_formats:
                self.logs[cur_format].append(log.get_body(cur_format))

    def table(self, data: list[list[any]], index=False, header=False):
        """
        Adds a table to the log.

        :param data: The table data. A list of rows including a list of
            columns.

            Each row has to provide the same count of columns.

            At the moment only string content is supported.
        :param index: Defines if the table has an index column
        :param header: Defines if the table has a header
        """
        code = '<table class="log_table">\n'
        for row_index, row in enumerate(data):
            tabs = "\t"
            code += f"{tabs}<tr>\n"
            for col_index, col in enumerate(row):
                code += f"\t{tabs}<td>\n{tabs}\t"
                assert isinstance(col, str)  # more types to be supported soon
                if index and col == 0:
                    code += "<b>"
                major_cell = (row_index == 0 and header or
                              col_index == 0 and index)
                if major_cell:
                    code += f"<b>{col}</b>"
                else:
                    code += col
                if index and col == 0:
                    code += "</b>"
                code += f"\n{tabs}</td>\n"
                tabs = tabs[0:-1]
            code += f"{tabs}</tr>\n"
        code += "</table>\n"
        self._add_html(code)
        for row in data:
            row_text = "| "
            for index, col in enumerate(row):
                row_text += col + " | "
            self._add_txt(row_text, md=True)
        return self

    def image(self, source: Image | Canvas | str | bytes | np.ndarray,
              name: str | None = None,
              alt_text: str | None = None,
              pixel_format: Optional["PixelFormat"] | str | None = None,
              download: bool = False,
              scaling: float = 1.0,
              max_width: int | float | None = None,
              optical_scaling: float = 1.0,
              html_linebreak=True):
        """
        Writes the image to disk for manual verification

        :param name: The name of the image under which it shall be stored
            on disk (in case write_to_disk is enabled).
        :param source: The data object, e.g. an scitag.imagestag.Image, a
            numpy array, an URL or a FileStag compatible link.
        :param alt_text: An alternative text if no image can be displayed
        :param pixel_format: The pixel format (in case the image is passed
            as numpy array). By default gray will be used for single channel,
            RGB for triple band and RGBA for quad band sources.
        :param download: Defines if an image shall be downloaded
        :param scaling: The factor by which the image shall be scaled
        :param max_width: Defines if the image shall be scaled to a given size.

            Possible values
            - True = Scale to the log's max_fig_size.
            - float = Scale the image to the defined percentual size of the
                max_fig_size, 1.0 = max_fig_size

        :param optical_scaling: Defines the factor with which the image shall
            be visualized on the html page without really rescaling the image
            itself and thus giving the possibility to zoom in the browser.
        :param html_linebreak: Defines if a linebreak shall be inserted after
            the image.
        """
        if not self.log_images:
            return
        if name is None:
            name = "image"
        if alt_text is None:
            alt_text = name
        if self.log_txt_images or max_width is not None:
            download = True
        if isinstance(source, np.ndarray):
            source = Image(source, pixel_format=pixel_format)
        html_lb = "<br>" if html_linebreak else ""
        if isinstance(source, str):
            if not source.lower().startswith("http") or download or \
                    self.embed_images:
                source = Image(source=source)
            else:
                self._insert_image_reference(name, source, alt_text, scaling,
                                             html_linebreak)
                return
        self.name_counter[name] += 1
        filename = name
        if self.name_counter[name] > 1:
            filename += f"__{self.name_counter[name]}"
        if isinstance(source, Canvas):
            source = source.to_image()
        file_location = ""
        size_definition = ""
        if scaling != 1.0 or optical_scaling != 1.0 or max_width is not None:
            max_size = None
            if max_width is not None:
                if scaling != 1.0:
                    raise ValueError(
                        "Can't set max_size and scaling at the same time.")
                scaling = None
                if isinstance(max_width, float):
                    max_width = int(round(self.max_fig_size.width * max_width))
                max_size = (max_width, None)
            if not isinstance(source, Image):
                source = Image(source)
            source = source.resized_ext(factor=scaling, max_size=max_size)
            size_definition = \
                f" width={int(round(source.width * optical_scaling))} " \
                f"height={int(round(source.height * optical_scaling))}"
        # encode image if required
        if isinstance(source, bytes):
            encoded_image = source
        else:
            encoded_image = source.encode(
                filetype=self.image_format,
                quality=self.image_quality)
        # store on disk if required
        if self.log_to_disk:
            file_location = self._log_image_to_disk(filename, name, source,
                                                    encoded_image)
        # embed if required
        if self.embed_images:
            embed_data = self._build_get_embedded_image(encoded_image)
            file_location = embed_data
        if len(file_location):
            self._add_html(
                f'<img src="{file_location}" {size_definition}>{html_lb}\n')
        if self.log_txt_images and self.txt_export:
            if not isinstance(source, Image):
                source = Image(source)
            max_width = min(max(source.width / 1024 * 80, 1), 80)
            self._add_txt(source.to_ascii(max_width=max_width))
            self._add_txt(f"Image: {alt_text}\n")
        else:
            self._add_txt(f"\n[IMAGE][{alt_text}]\n")
        self._log.clip_logs()

    def _insert_image_reference(self,
                                name,
                                source,
                                alt_text,
                                scaling: float = 1.0,
                                html_scaling: float = 1.0,
                                html_linebreak: bool = True):
        """
        Inserts a link to an image in the html logger without actually
        downloading or storing the image locally

        :param name: The image's name
        :param source: The url
        :param alt_text: The alternative display text
        :param scaling: The scaling factor
        :param html_scaling: Defines the factor with which the image shall
            be visualized on the html page without really rescaling the image
            itself and thus giving the possibility to zoom in the browser.
        :param html_linebreak: Defines if a linebreak shall be inserted
            after the image
        """
        html_lb = "<br>" if html_linebreak else ""
        if scaling != 1.0 or html_scaling != 1.0:
            image = Image(source)
            width, height = (int(round(image.width * scaling * html_scaling)),
                             int(round(image.height * scaling * html_scaling)))
            self._add_html(
                f'<img src="{source}" with={width} height={height}>{html_lb}')
        else:
            self._add_html(f'<img src="{source}">{html_lb}')
        self._add_md(f'![{name}]({source})\n')
        self._add_txt(f"\n[IMAGE][{alt_text}]\n")

    def _log_image_to_disk(self,
                           filename: str,
                           name: str,
                           source: bytes | Image,
                           encoded_image) -> str:
        """
        Stores an image on the disk

        :param filename:  The output filename
        :param name:  The image's name
        :param source: The data source
        :param encoded_image: The encoded image
        :return: The file location of the store image
        """
        file_location = ""
        if isinstance(source, bytes):
            import filetype
            file_type = filetype.guess(source)
            target_filename = (self.target_dir +
                               f"/{filename}.{file_type.extension}")
            if self._need_to_store_images_on_disk():
                FileStag.save(target_filename, source)
        else:
            extension = (self.image_format if
                         isinstance(self.image_format, str)
                         else self.image_format[0])
            target_filename = \
                self.target_dir + f"/{filename}.{extension}"
            if self._need_to_store_images_on_disk():
                FileStag.save(target_filename, encoded_image)
        if not self.embed_images:
            file_location = FilePath.basename(target_filename)
        if self.md_export:
            self._add_md(
                f'![{name}]({FilePath.basename(target_filename)})\n')
        return file_location

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
        import inspect
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
        if not isinstance(text, str):
            text = str(text)
        for element in self.forward_targets.values():
            element.text(text)
        lines = html.escape(text)
        lines = lines.split("\n")
        for index, text in enumerate(lines):
            self._add_html(f'{text}<br>\n')
            if index == len(lines) - 1:
                self._add_md(f"{text}")
            else:
                self._add_md(f"{text}\\")
            self._add_txt(text)
        self.clip_logs()

    def line_break(self):
        """
        Inserts a simple line break
        """
        self._add_html("<br>")
        self._add_txt(" ", md=True)

    def page_break(self):
        """
        Inserts a page break
        """
        self._add_html('<div style="break-after:page"></div>')
        self._add_txt(
            f"\n{'_' * 40}\n",
            md=True)

    def sub(self, text: str, level: int = 2):
        """
        Adds a sub title to the log

        :param text: The text to add to the log
        :param level: The title level (0..5)
        :return: Self
        """
        assert 0 <= level <= 5
        for element in self.forward_targets.values():
            element.sub(text)
        md_level = "#" * level
        escaped_lines = html.escape(text)
        for cur_row in escaped_lines.split("\n"):
            self._add_html(f'<h{level}>{cur_row}</h{level}>\n')
        self._add_md(f"{md_level} {text}")
        if self._add_txt(text) and level <= 4:
            character = "=" if level < 2 else "-"
            self._add_txt(character * len(text))
        self._add_txt("")
        self.clip_logs()
        return self

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
        Adds a subtest section to the log

        :param text: The text to add to the log
        :return:
        """
        self.sub(text, level=4)

    def md(self, text: str, exclude_targets: set[str] | None = None):
        """
        Adds a markdown section.

        Requires the Markdown package to be installed.

        :param text: The text to parse
        :param exclude_targets: Defines the target to exclude
        """
        if exclude_targets is None:
            exclude_targets = set()
        for element in self.forward_targets.values():
            element.md(text)
        import markdown
        parsed = markdown.markdown(text)
        if MD not in exclude_targets:
            self._add_md(text + "\n")
        if HTML not in exclude_targets:
            self._add_html(parsed + "\n")
        if TXT not in exclude_targets:
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
        self._add_html(code + "\n")
        self.clip_logs()

    def code(self, code: str):
        """
        Adds code to the log
        :param code: The code to execute
        """
        for element in self.forward_targets.values():
            element.code(code)
        escaped_code = html.escape(code).replace("\n", "<br>")
        self._add_html(f'Code<br><table class="source_code"\n>'
                       f'<tr><td style="padding: 5px;" align="left">\n'
                       f'<code>{escaped_code}</code>\n'
                       f'</td></tr></table><br><br>\n')
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

    def _log_advanced(self, text, level: LogLevel):
        """
        Detects tables and other objects in a log and pretty prints the tables
        while keeping the other log data intact

        :param text: The log text
        :param level: The log level
        """
        lines = text.split("\n")
        common_block = ""
        cur_table = None
        for line in lines:
            if line.startswith(TABLE_PIPE):
                if len(common_block) > 0:
                    self.log(common_block, level=level)
                    common_block = ""
                if cur_table is None:
                    cur_table = []
                elements = [element.lstrip(" ").rstrip(" ") for element in
                            line.split("|")]
                if len(elements) > 2:
                    elements = elements[1:-1]
                cur_table.append(elements)
            else:
                # when back to normal mode visualize current in-progress element
                if cur_table is not None:
                    self.table(cur_table)
                    cur_table = None
                common_block += line + "\n"
        if len(common_block) > 0:
            self.log(common_block, level=level)

    def log(self, *args: Any, level: LogLevel | str = LogLevel.INFO,
            detect_objects: bool = False,
            space: str = " "):
        """
        Adds a log text to the log

        :param args: The text arguments to add to the log
        :param level: The importance / category of the log entry
        :param detect_objects: Defines if special objects such as tables shall
            be detected and printed beautiful
        :param space: The character or text to be used for spaces
        :return:
        """
        if isinstance(level, str):
            level = LogLevel(level)
        elements = [str(element) for element in args]
        text = space.join(elements)
        if detect_objects and TABLE_PIPE in text:
            self._log_advanced(text, level)
            return
        if text is None:
            text = "None"
        if not isinstance(text, str):
            text = str(text)
        for element in self.forward_targets.values():
            element.log(text, level=level)
        escaped_text = self._encode_html(text)
        self._add_html(
            f'<p class="logtext">{self._html_linebreaks(escaped_text)}</p>'
            f'<br>\n')
        if MD in self.logs and len(self.logs[MD]) > 0:
            last_md_log: str = self.logs[MD][-1].decode("utf-8")
            if last_md_log.endswith("```\n"):
                self._add_md(f"{text}\n```")
        else:
            self._add_md(f"```\n{text}\n```")
        self._add_txt(text)
        self.clip_logs()

    def log_timestamp(self, prefix: str = "", postfix: str = ""):
        """
        Logs a timestamp to the log

        :param prefix: The text before the timestamp
        :param postfix: The text after the timestamp
        :return:
        """
        from datetime import datetime
        dt_object = datetime.now()
        cur_time = f"{str(dt_object.date())} {str(dt_object.time())}"
        elements = [cur_time]
        if len(prefix) > 0:
            elements.insert(0, prefix)
        if len(postfix) > 0:
            elements.append(postfix)
        self.log("".join(elements))

    def get_statistics(self) -> dict:
        """
        Returns statistics about the log

        :return: A dictionary with statistics about the log such as
            - totalUpdateCount - How often was the log updated?
            - updatesPerSecond - How often was the log updated per second
            - upTime - How long is the log being updated?
        """
        return {"totalUpdateCount": self._total_update_counter,
                "updatesPerSecond": self._update_rate,
                "upTime": time.time() - self._log.start_time}

    def log_statistics(self):
        """
        Adds statistics about the VisualLog as table to the log
        """
        self.table([["Updates", f"{self._total_update_counter} total updates"],
                    ["Effective lps",
                     f"{self._update_rate:0.2f} updates per second"],
                    ["Uptime",
                     f"{time.time() - self._log.start_time:0.2f} seconds"]],
                   index=True)

    def df(self, df: pd.DataFrame, name: str | None = None, index: bool = True):
        """
        Adds a dataframe to the log

        :param name: The dataframe's name
        :param df: The data frame
        :param index: Defines if the index shall be printed
        """
        if name is None:
            name = "dataframe"
        for element in self.forward_targets.values():
            element.df(name=name, df=df, index=index)
        if self._log.use_pretty_html_table:
            try:
                import pretty_html_table
                html_code = \
                    pretty_html_table.build_table(df,
                                                  self._log.html_table_style,
                                                  index=index)
            except ModuleNotFoundError:  # pragma: no-cover
                html_code = df.to_html(index=index)
        else:
            html_code = df.to_html(index=index)
        self._add_html(html_code + "\n")
        if self._log.use_tabulate:
            try:
                import tabulate
                md_table = df.to_markdown(index=index,
                                          tablefmt=self._log.md_table_format)
                self._add_md(md_table)
                self._add_txt(
                    df.to_markdown(index=index,
                                   tablefmt=self._log.txt_table_format) + "\n")
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
        self._log.clip_logs()

    def figure(self, figure: plt.Figure | plt.Axes | Figure | Plot,
               name: str | None = None,
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
        if name is None:
            name = "figure"
        if not self.log_images and _out_image_data is None:
            return
        if isinstance(figure, (Figure, Plot)):
            image = figure.render()
            self.image(image, name, alt_text=alt_text)
            if _out_image_data is not None:
                _out_image_data.write(
                    image.encode(filetype=self.image_format,
                                 quality=self.image_quality))
            return
        if not isinstance(figure, plt.Figure):
            figure = figure.figure
        image_data = MPHelper.figure_to_png(figure, transparent=False)
        if _out_image_data is not None:
            _out_image_data.write(image_data)
        self.image(image_data, name, alt_text=alt_text)

    def pyplot(self) -> "PyPlotLogContext":
        """
        Opens a matplotlib context to add a figure directly to the plot.

        Also takes care off that no other thread is using matplotlib so you
        can safely plot using this function and matplotlib from multiple
        threads at once.

        ..  code-block:

            with vl.pyplot() as plt:
                figure = plt.figure(figsize=(8,4))
                plt.imshow(some_image_matrix)
        """
        from scistag.logstag.visual_log.pyplot_log_context import \
            PyPlotLogContext
        log_context = PyPlotLogContext(self)
        return log_context

    def log_dict(self, dict_or_list: dict | list):
        """
        Logs a dictionary or a list.

        The data needs to be JSON compatible so can contain further nested
        diotionaries, lists, floats, booleans or integers but no more
        complex types.

        :param dict_or_list: The dictionary or list
        """
        from scistag.common.dict_helper import dict_to_bullet_list
        dict_tree = dict_to_bullet_list(dict_or_list, level=0, bold=True)
        self.md(dict_tree, exclude_targets={'txt'})
        if self.txt_export:
            dict_tree_txt = dict_to_bullet_list(dict_or_list, level=0,
                                                bold=False)
            self._add_txt(dict_tree_txt)

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
                f"⚠️Hash validation failed!\nValue: "
                f"{value}\nAssumed: {assumed}")
            self._log.write_to_disk()
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
        Adds a figure to the log and verifies its content to a checksum

        :param name: The figure's name
        :param figure: The figure to log
        :param alt_text: An alternative text to display if the figure can
            not be displayed.
        :param hash_val: The hash value to compare to (a checksum of all
            pixels). The correct will be logged via an assertion upon failure
            and can then be copies & pasted.
        """
        image_data = io.BytesIO()
        self.figure(figure=figure, name=name, alt_text=alt_text,
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
        self.image(source=data, name=name, alt_text=alt_text, scaling=scaling)
        return data.get_hash()

    def assert_text(self, name: str, text: str, hash_val: str):
        """
        Asserts a text for validity and logs it

        :param name: The assertion's name
        :param text: The text data
        :param hash_val: The assumed hash value
        """
        _ = name
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
        :param dump: Defines if the data frame shall be dumped to disk.
            To this once for a new data frame to create a reference
        :param hash_val: If specified the dataframe will get dumped as csv
            of which the hash value is compared to the one passed.
        """
        if hash_val is not None:
            output = io.BytesIO()
            df.to_csv(output)
            result_hash_val = hashlib.md5(output.getvalue()).hexdigest()
            if result_hash_val != hash_val:
                self._log.write_to_disk()
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
                self._log.write_to_disk()
                raise AssertionError("Hash mismatch - "
                                     f"Found: {result_hash_val} - "
                                     f"Assumed: {hash_val}")
            return
        if dump:
            output = io.BytesIO()
            # noinspection PyTypeChecker
            np.save(output, data)
            self.save_ref(name, output.getvalue())
            print(f"Warning - Updating test reference of {name}")
        comp_data = self.load_ref(name)
        if comp_data is None:
            raise AssertionError(f"No reference data provided for {name}")
        # noinspection PyTypeChecker
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
            import json
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
        FilePath.make_dirs(self.ref_dir, exist_ok=True)
        hash_fn = self.ref_dir + "/" + hashed_name + ".dmp"
        FileStag.save(hash_fn, data)

    def load_ref(self, name: str) -> bytes | None:
        """
        Loads the data reference

        :param name: The reference's unique name
        :return: The data. None if no reference could be found
        """
        hashed_name = self._get_hashed_filename(name)
        hash_fn = self.ref_dir + "/" + hashed_name + ".dmp"
        if FileStag.exists(hash_fn):
            return FileStag.load(hash_fn)
        return None

    @staticmethod
    def _get_hashed_filename(name):
        """
        Returns a hashed filename for name to be store it with a fixed size
        on disk

        :param name: The file's name
        :return: The hash name to be used as filename
        """
        hashed_name = hashlib.md5(name.encode('utf-8')).hexdigest()
        return hashed_name

    @staticmethod
    def _html_linebreaks(text: str) -> str:
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
        self._log.write_html(html_code)

    def _add_md(self, md_code: str, no_break: bool = False):
        """
        The markdown code to add

        :param md_code: The markdown code
        :param no_break: If defined no line break will be added
        :return: True if txt logging is enabled
        """
        self._log.write_md(md_code, no_break=no_break)

    def _add_txt(self, txt_code: str, console: bool = True, md: bool = False):
        """
        Adds text code to the txt / console log

        :param txt_code: The text to add
        :param console: Defines if the text shall also be added ot the
            console's log (as it's mostly identical). True by default.
        :param md: Defines if the text shall be added to markdown as well
        :return: True if txt logging is enabled
        """
        self._log.write_txt(txt_code, console, md)

    def clip_logs(self):
        """
        Clips the logging files (e.g. if they are limited in length)
        """
        self._log.clip_logs()

    def _need_to_store_images_on_disk(self) -> bool:
        """
        Returns if images NEED to be stored on disk

        :return: True if they do
        """
        return self.md_export or not self.embed_images
