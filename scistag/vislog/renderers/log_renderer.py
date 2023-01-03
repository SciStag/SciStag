"""
Implements the class :class:`LogRenderer` which defines an abstract
base interface for different logging output file types.
"""

from __future__ import annotations

from scistag.optional.jinja_opt import jinja_available, jinja2
from scistag.vislog.visual_log import MAIN_LOG


class LogRenderer:
    """
    Defines an abstract interface for adding data to a log of any format
    """

    def __init__(self):
        if not jinja_available():
            assert ModuleNotFoundError(
                "VisualLog with needs the "
                "installed Jinja2, e.g. via pip install "
                "scistag[logstag], pip install "
                "logstag or pip install Jinja2"
            )
        self.body_template = ""
        "The original body template to be parsed by Jinja"
        self.body_template_rendered = ""
        "The rendered template with only place holders for content remaining"
        self.title = "Visual Live Log"
        "The pages title"
        self.header_template: str = ""
        "The template for the top of the page"
        self.footer_template: str = ""
        "The template for the foot of the page"
        self.header_rendered: bytes = b""
        "The encoded and rendered header"
        self.footer_rendered: bytes = b""
        "The encoded and rendered footer"

    def get_rendering_variables(self):
        """
        Returns the variables use to render the templates

        :return: A dictionary with all variables
        """
        import scistag

        return {
            "title": self.title,
            "scistag_version": scistag.__version__,
        }

    def set_body_template(self, template: str, **params):
        """
        Changes the current body template

        :param template: The new Jinja template
        :param sub_logs: The names of the sub logs to be inserted
        :param params: Optional creation parameters
        """
        assert template is not None
        self.body_template = template
        environment = jinja2.Environment()
        template = environment.from_string(self.body_template)
        self.body_template_rendered = template.render(
            **self.get_rendering_variables(), **params
        )

    def set_header_template(self, template: str, **params):
        """
        Sets a new header template

        :param template: The template's string data
        :param params: Parameters of content to be inserted
        """
        assert template is not None
        self.header_template = template
        environment = jinja2.Environment()
        template = environment.from_string(self.header_template)
        self.header_rendered = template.render(
            **self.get_rendering_variables(), **params
        ).encode("utf-8")

    def set_footer_template(self, template: str, **params):
        """
        Sets a new footer template

        :param template: The template's string data
        :param params: Parameters of content to be inserted
        """
        assert template is not None
        self.footer_template = template
        environment = jinja2.Environment()
        template = environment.from_string(self.footer_template)
        self.footer_rendered = template.render(
            **self.get_rendering_variables(), **params
        ).encode("utf-8")

    def build_page(self, body, custom_code) -> bytes:
        """
        Combines the head's header, body and footer to a full html page

        :param body: The page's body
        :param custom_code: Custom code to be inserted
        :return: The full, deliverable page
        """
        return b"".join([self.header_rendered, custom_code, body, self.footer_rendered])

    def build_body(self, log_data: bytes) -> bytes:
        """
        Assembles the sub logs and uses the body pieces to combine it to
        a delivarable files

        :param log_data: The log data
        :return: The final file data
        """
        return log_data
