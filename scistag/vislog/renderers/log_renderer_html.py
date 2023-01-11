"""
Defines the class :class:`HtmlLogRenderer` which implements a log
renderer for HTML.
"""
from __future__ import annotations

from scistag.filestag import FileStag, FilePath
from scistag.vislog.options import LogOptions
from scistag.vislog.visual_log import MAIN_LOG
from scistag.vislog.renderers.log_renderer import LogRenderer


class HtmlLogRenderer(LogRenderer):
    """
    VisualLog plugin for creating HTML files

    HtmlLogRenderer and will be removed soon.
    TODO: Remove me
    """

    def __init__(self, title: str = "SciStag VisualLog", options: LogOptions = None):
        """
        :param title: The log's title
        """
        super().__init__(options)
        self.title = title

        new_body_template = FileStag.load_text(
            FilePath.absolute_comb("../templates/staticLog/default_log.html")
        )
        self.set_body_template(new_body_template, sub_logs=[MAIN_LOG])
        new_header_template = FileStag.load_text(
            FilePath.absolute_comb("../templates/base_header.html")
        )
        self.set_header_template(new_header_template)
        new_footer_template = FileStag.load_text(
            FilePath.absolute_comb("../templates/base_footer.html")
        )
        self.set_footer_template(new_footer_template)

    def set_header_template(self, template: str, **params):
        super().set_header_template(template, **params)
