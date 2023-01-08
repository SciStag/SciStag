"""
Defines the configuration options for VisualLog and associated classes
"""
from __future__ import annotations
from typing import Union, Literal

from pydantic import BaseModel, Field

from scistag.imagestag import Size2DTypes
from scistag.vislog.options import LSliderOptions
from scistag.vislog.options.table_options import LogTableOptions
from scistag.webstag.server_options import ServerOptions


class HtmlClientDebugOptions(BaseModel):
    """
    Html client debug options
    """

    log_updates: bool = False
    """Defines if modifications to the dom structure shall be logged"""


class LogDebugOptions(BaseModel):
    """
    Debug options
    """

    html_client: HtmlClientDebugOptions = Field(default_factory=HtmlClientDebugOptions)

    def enable(self):
        """
        Enabled a standard debugging options set
        """
        self.html_client.log_updates = True

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """


class LogImageOptions(BaseModel):
    """
    Image and figure default configurations
    """

    class Config:
        arbitrary_types_allowed = True

    embed_images: Union[bool, None] = (None,)
    """Defines if images shall be directly embedded into
        the HTML log instead of being stored as separate files.

        By default True if Markdown is not set as one of the "formats_out",
        otherwise False by default as Markdown will need the files on disk."""
    default_filetype: Union[str, tuple[str, int]] = "png"
    """The default output image format to store images
        and figures with. "png" by default.

        You can also pass the image format and image quality in a tuple
        such as ("jpg", 60).

        Alternatively "jpg" or "bmp" can be used (to minimize the bandwidth
        or in the later case if you are the intranet w/ unlimited bandwidth
        and want to host it live at maximum performance)."""
    max_fig_size: Union[Size2DTypes, None] = None
    """The optimum, maximum width and height for embedded figures and images"""


class LogStyleOptions(BaseModel):
    """
    Defines the default style for all elements
    """

    slider: LSliderOptions = Field(default_factory=LSliderOptions)
    """Default options for a slider"""
    table: LogTableOptions = Field(default_factory=LogTableOptions)
    """Default options for a table"""
    image: LogImageOptions = Field(default_factory=LogImageOptions)

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """


class LogRunOptions(BaseModel):
    """
    Options for defining the running behavior of the log, e.g. if it shall be run once
    or continuous.
    """

    mt: bool = True
    """
    Defines if the server shall be run in multithreading mode
    """
    continuous: Union[bool, None] = None
    """
    Defines if the run_server shall run until
    :meth:`LogBuilder.terminate` was called to update the logs content
    continuously."""
    wait: bool = True
    """Defines if also a non-continuous log shall wait till
    the log has been terminated. (via :meth:`terminate`) or the
    application was killed via Ctrl-C.

    Has no effect if threaded is False (because the server will anyway
    block the further execution then) or if continuous is set to True.

    Basically it acts like the "continuous" mode just with the
    difference that the builder function is just called once."""
    auto_clear: Union[bool, None] = None
    """Defines if then log shall be cleared automatically
    when being rebuild with `continuous=True`."""

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """


class LogServerOptions(ServerOptions):
    show_urls: bool = True
    """Defines if the URLs at which the server can be reached shall be shown upon 
    start"""

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
        super().validate_options()


class LogOutputOptions(BaseModel):
    """
    Defines which types of output the LogBuilder shall generate, if and where to store
    this output on disk.
    """

    target_dir: str = "./logs"
    """The output directory"""
    index_name: str = "index"
    """Defines the name of the log's index file. index by
        default.

        Extensions such as .html, .md and .txt will automatically
        be added."""
    log_to_disk: bool = False
    """Defines if the logger shall write it's results to disk. False by default."""
    log_to_stdout: bool = False
    """Defines if the system shall automatically log to stdout via print as well"""
    ref_dir: Union[str, None] = None
    """The directory in which the reference data objects can be stored."""
    tmp_dir: Union[str, None] = None
    """A directory in which temporary files can be stored. Will be deleted upon 
    finalization."""
    clear_target_dir: bool = False
    """Defines if the target dir shall be deleted before starting (take care!)"""
    formats_out: Union[set[str], None] = Field(default_factory=lambda: {"html"})
    """A set of the formats to export.

        "html", "txt" (pure Text)  and "md" (markdown) are supported.

        By default only html files will be created."""
    single_file: bool = True
    """Defines if all content of the (non-live) output file shall be stored in a
    single file"""

    def setup(
        self,
        disk: bool | None = None,
        console: bool | None = None,
        formats: set[str] = None,
        single_file: bool | None = None,
        index_name: str | None = None,
        target_dir: str | None = None,
        clear_target_dir: bool | None = None,
    ):
        """
        Returns the default output options

        :param disk: Defines if the results shall be logged to disk
        :param console: Defines if the log shall write to the console
        :param single_file: Defines if the output (of each output type) shall be
            stored in a single file.
        :param formats: Defines the output formats such as "html", "md" and "txt"
        :param index_name: The index's name
        :param target_dir: Defines the directory in which the output logs shall be
            stored.
        :param clear_target_dir: Defines if the output directory shall be cleared,
            target care there are no important files in the target directory defined.
        :return: self
        """
        if formats is not None:
            self.formats_out = formats
        if disk is not None:
            self.log_to_disk = disk
        if single_file is not None:
            self.single_file = single_file
        if console is not None:
            self.log_to_stdout = console
        if index_name is not None:
            self.index_name = index_name
        if target_dir is not None:
            self.target_dir = target_dir
        if clear_target_dir is not None:
            self.clear_target_dir = clear_target_dir

        return self

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """


class LogOptions(BaseModel):
    """
    Defines the configuration of a VisualLog
    """

    output: LogOutputOptions = Field(default_factory=LogOutputOptions)
    """Output specific options such as where to store the log and in which formats"""
    run: LogRunOptions = Field(default_factory=LogRunOptions)
    """Execution options such as if the execution shall be done in a parallel thread"""
    server: LogServerOptions = Field(default_factory=LogServerOptions)
    """Server configuration flags, e.g. hosting IPs, port etc."""
    style: LogStyleOptions = Field(default_factory=LogStyleOptions)
    """Advanced style configuration"""
    debug: LogDebugOptions = Field(default_factory=LogDebugOptions)
    """Debug options"""

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
        self.output.validate_options()
        self.run.validate_options()
        self.server.validate_options()
        self.style.validate_options()
        self.debug.validate_options()

    def setup_defaults(
        self,
        defaults: Literal["local", "server", "disk", "console", "disk&console"]
        | None = None,
    ) -> LogOptions:
        """
        Applies one of the standard configurations to the option sets depending on
        your main use case.

        :param defaults: Defines the default configuration which shall be applied to
            the option set. See :meth:`VisualLog.setup_options` for further details.
        """
        if defaults is None or defaults == "local":
            pass
        elif defaults == "disk":
            self.output.setup(disk=True, console=False)
        elif defaults == "console":
            self.output.setup(disk=False, console=True)
        elif defaults == "disk&console":
            self.output.setup(disk=True, console=True)
        elif defaults == "server":
            self.output.setup(disk=False, console=False)
            self.server.setup_server_defaults()
        else:
            raise ValueError(
                'Missing default options parameter. Define one of "local", "server", '
                '"console", "disk" or "disk&console" to select the standard '
                "configuration."
            )
        return self
