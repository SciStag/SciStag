"""
Defines the configuration options for VisualLog and associated classes
"""
from __future__ import annotations
from typing import Literal, Union
from pydantic import BaseModel, Field


from scistag.vislog.options.cache_options import CacheOptions
from scistag.vislog.options.debug_options import LogDebugOptions
from scistag.vislog.options.extension_options import ExtensionOptions
from scistag.vislog.options.format_options import FormatOptions
from scistag.vislog.options.page_options import PageOptions
from scistag.vislog.options.style_options import LogStyleOptions
from scistag.vislog.options.run_options import LogRunOptions, APP_MODES
from scistag.vislog.options.log_server_options import LogServerOptions
from scistag.vislog.options.output_options import OutputOptions
from scistag.imagestag import Size2DTypes, Size2D

LOG_DEFAULT_OPTION_LITERALS = Literal[
    "server", "local", "disk", "console", "disk&console"
]
"""Enumeration of default option set string identifiers"""


class LogOptions(BaseModel):
    """
    Defines the configuration of a VisualLog
    """

    page: PageOptions = Field(default_factory=PageOptions)
    """Defines the initial page setup"""
    output: OutputOptions = Field(default_factory=OutputOptions)
    """Output specific options such as where to store the log and in which formats"""
    run: LogRunOptions = Field(default_factory=LogRunOptions)
    """Execution options such as if the execution shall be done in a parallel thread"""
    server: LogServerOptions = Field(default_factory=LogServerOptions)
    """Server configuration flags, e.g. hosting IPs, port etc."""
    style: LogStyleOptions = Field(default_factory=LogStyleOptions)
    """Advanced style configuration"""
    debug: LogDebugOptions = Field(default_factory=LogDebugOptions)
    """Debug options"""
    formats: FormatOptions = Field(default_factory=FormatOptions)
    """File format specific options"""
    cache: CacheOptions = Field(default_factory=CacheOptions)
    """The cache configuration"""
    extensions: ExtensionOptions = Field(default_factory=ExtensionOptions)
    """Extension configuration. Allows enabling advanced features"""

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
        self.output.validate_options()
        self.run.validate_options()
        self.server.validate_options()
        self.style.validate_options()
        self.debug.validate_options()
        self.page.validate_options()
        self.formats.validate_options()
        self.cache.validate_options()
        self.extensions.validate_options()

    def setup_defaults(
        self,
        defaults: Literal["local", "server", "disk", "console", "disk&console"]
        | None = None,
        title: str | None = None,
        index_name: str | None = None,
    ) -> LogOptions:
        """
        Applies one of the standard configurations to the option sets depending on
        your main use case.

        :param defaults: Defines the default configuration which shall be applied to
            the option set. See :meth:`VisualLog.setup_options` for further details.
        :param title: The log's initial title
        :param index_name: The name of the index file (without extension)
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
        if title is not None:
            self.page.title = title
        if index_name is not None:
            self.output.index_name = index_name
        return self

    def configure_sub_log(self):
        """
        Removes all writing actions from this options.

        This is used to configure a log which is going to be embedded in another log
        anyway and thus shall just share the format and styling options.
        """
        self.output.log_to_disk = False
        self.output.log_to_stdout = False
        self.server.host_name = ""
        self.server.port = 0

LogOptions.model_rebuild()