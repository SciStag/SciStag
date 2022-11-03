"""
Defines the class :class:`VisualLogHtmlRenderer` which implements a log
renderer for HTML.
"""
from __future__ import annotations

import os

from scistag.filestag import FileStag, FilePath
from scistag.logstag.visual_log.visual_log import MAIN_LOG
from scistag.logstag.visual_log.visual_log_renderer import VisualLogRenderer


class VisualLogHtmlRenderer(VisualLogRenderer):
    """
    VisualLog plugin for creating HTML files
    """

    def __init__(self, title: str = "SciStag VisualLog"):
        """
        :param title: The log's title
        """
        super().__init__()
        self.title = title
        self.css = FileStag.load_text(
            os.path.dirname(__file__) + "/css/visual_log.css")

        new_body_template = \
            FileStag.load_text(FilePath.absolute_comb(
                "templates/staticLog/default_log.html"))
        self.set_body_template(new_body_template,
                               sub_logs=[MAIN_LOG])
        new_header_template = \
            FileStag.load_text(FilePath.absolute_comb(
                "templates/base_header.html"))
        self.set_header_template(new_header_template)
        new_footer_template = \
            FileStag.load_text(FilePath.absolute_comb(
                "templates/base_footer.html"))
        self.set_footer_template(new_footer_template)

    def set_header_template(self, template: str, **params):
        super().set_header_template(template, css=self.css, **params)
