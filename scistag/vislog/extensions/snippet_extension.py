"""
The snippet extension allows recording outputs to the log and to "replay them", so
insert them at different locations in the log.

This way you can for example prepare all your plots in a separate location and insert
them where needed.
"""
from __future__ import annotations

from typing import List

from scistag.vislog import LogBuilder, BuilderExtension


class SnippetRecording:
    """
    Contains the data recorded for the snippet
    """

    def __init__(self, data: dict[str, bytes]):
        """
        :param data: The data for each output format
        """

        self.data: dict[str, bytes] = data
        """Contains the log data for the different output formats"""

    def get(self, out_format: str, default=b""):
        """
        Returns data for given format.

        Returns the defined default value if the format does not exist

        :param out_format: The desired output format, e.g. html
        :param default: The default return value
        :return: The data as bytes string
        """
        return self.data.get(out_format, b"")

    def __getitem__(self, item) -> bytes:
        """
        Returns the data for given format

        :param item: The format name
        :return: The content
        """
        return self.data[item]

    def __contains__(self, item):
        """
        Returns if given format is supported

        :param item: The format
        :return: True if the format is known
        """
        return item in self.data


class SnippetContext:
    """
    Helps to record log output to for example insert it multiple times or delayed.

    While the context is active no data is added to the real log, also the embedding
    mode is temporarily enforced to ensure all data will be stored in the recording
    itself.
    """

    def __init__(self, builder: LogBuilder):
        """
        :param builder: The builder which we shall record
        """
        self.builder = builder
        """The builder being recorded"""
        from scistag.vislog.common.log_element import LogElement

        self.log_element = LogElement(
            name="root", output_formats=self.builder.options.output.formats_out
        )
        self.embed_state: bool = False
        self.recording: SnippetRecording | None = None
        """The recording result data"""

    def __enter__(self):
        self.builder.page_session.enter_element(self.log_element)
        self.embed_state = self.builder.options.style.image.embed_images
        self.embed_state = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.builder.page_session.end_sub_element()
        self.builder.options.style.image.embed_images = self.embed_state
        data = {}
        for key in self.log_element.data.keys():
            data[key] = self.log_element.build(key)
        self.recording = SnippetRecording(data=data)


class SnippetExtension(BuilderExtension):
    """
    The snippet extension allows recording output to the log (without actually really
    inserting it) to insert it at a later point and/or multiple times.
    """

    def __init__(self, builder: LogBuilder):
        """
        :param builder: The builder object
        """
        super().__init__(builder)
        self._context_stack: List[SnippetContext] = []
        """Current context stag"""

    def __call__(self) -> SnippetContext:
        """
        Creates a SnippetContext into which log data can be recorded

        :return: The recording
        """
        return SnippetContext(self.builder)

    def __enter__(self):
        context = SnippetContext(self.builder)
        self._context_stack.append(context)
        return context.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        last = self._context_stack.pop(-1)
        return last.__exit__(exc_type, exc_val, exc_tb)
