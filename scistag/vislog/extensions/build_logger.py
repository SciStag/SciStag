"""
Implements the BuildLogger which helps rendering other LogBuilders and to embed them
into the main log.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Union, Callable, Any

from pydantic import BaseModel

from scistag.vislog.extensions.builder_extension import BuilderExtension

if TYPE_CHECKING:
    from scistag.vislog.log_builder import LogBuilder


@dataclass
class BuilderRunResult:
    """
    Holds the execution result after the execution of a singleton LogBuilder
    """

    output: dict = field(default_factory=dict)
    """
    The log's output.
    
    In case of a standard LogBuilder this is a dictionary of all files which were
    generated by the log as filename, bytes tree.
    """


class BuildLogger(BuilderExtension):
    """
    Helper class for embedding other LogBuilders' results into the main log and
    processing data in parallel.
    """

    def __init__(self, builder: "LogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)

    def run(
        self,
        builder: type,
        full_page: bool = False,
        params: dict | BaseModel | Any | None = None,
        **kwargs,
    ):
        """
        Creates a temporary VisualLog with builder class builder, executes it and
        returns the content generated.

        :param builder: The builder class to be executed
        :param full_page: Defines if a full page shall be returned, including header
            and footer. False by default.
        :param params: Initial parameter set for the LogBuilder's params attribute,
            see :attr:`LogBuilder.params`.
        :param kwargs: Additional arguments to pass into the builder's constructor
        :return: The run results
        """
        from scistag.vislog import VisualLog

        log = VisualLog()
        log.run(builder=builder, params=params, nested=not full_page, **kwargs)
        result = BuilderRunResult()
        result.output = log.default_builder.get_result()
        return result
