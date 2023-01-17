from __future__ import annotations

from typing import Union

from pydantic import BaseModel, Field


class OutputOptions(BaseModel):
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
        from scistag.vislog import CONSOLE

        if formats is not None:
            if console:
                formats.add(CONSOLE)
            self.formats_out = formats
        else:
            if console:
                self.formats_out = {CONSOLE}
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
