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
            assert \
                ModuleNotFoundError("VisualLog with needs the "
                                    "installed Jinja2, e.g. via pip install "
                                    "scistag[logstag], pip install "
                                    "logstag or pip install Jinja2")
        self.body_template = ""
        "The original body template to be parsed by Jinja"
        self.body_template_rendered = ""
        "The rendered template with only place holders for content remaining"
        self.body_pieces: list[bytes | str] = []
        "The single (binary_) pre-rendered body pieces or place holder names"
        self.sub_log_names = [MAIN_LOG]
        """
        The names of the single sub logs to be inserted into the body template
        """
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
        return {"title": self.title,
                "scistag_version": scistag.__version__}

    def set_sub_logs(self, sub_logs):
        """
        Sets the new list of sub logs to be integrated

        :param sub_logs: The name of the sub logs to be integrated into the
            final page.
        """
        self.sub_log_names = sub_logs

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
        self.body_template_rendered = \
            template.render(**self.get_rendering_variables(), **params)
        self.build_body_pieces()

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
        self.header_rendered = \
            template.render(**self.get_rendering_variables(), **params).encode(
                "utf-8")

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
        self.footer_rendered = \
            template.render(**self.get_rendering_variables(), **params).encode(
                "utf-8")

    def build_body_pieces(self):
        """
        Slices the new html template into pieces which can be quickly assembled
        to the full page using pre-encoded binary data.
        """
        key_offsets = []
        key_names = [*list(self.sub_log_names), MAIN_LOG]
        key_names = list(set(key_names))
        body = self.body_template_rendered
        for sub_log_name in key_names:
            search_text = f"@{sub_log_name.upper()}_CONTENT"
            try:
                index = body.index(search_text)
            except IndexError:
                continue
            key_offsets.append((index, search_text, sub_log_name))
        # sort by index
        sorted_offsets = sorted(key_offsets, key=lambda x: x[0])
        last_end = -1
        self.body_pieces = []
        for cur_offset in sorted_offsets:
            next_index = cur_offset[0]
            next_length = len(cur_offset[1])
            self.body_pieces.append(
                body[last_end + 1:next_index].encode("utf-8"))
            last_end = next_index + next_length
            self.body_pieces.append(cur_offset[2])
        if last_end < len(body) + 1:
            self.body_pieces.append(body[last_end:].encode("utf-8"))

    def build_page(self, body) -> bytes:
        """
        Combines the head's header, body and footer to a full html page

        :param body: The page's body
        :return: The full, deliverable page
        """
        return b''.join(
            [self.header_rendered, body, self.footer_rendered])

    def build_body(self, sub_log_data: dict[str, bytes]) -> bytes:
        """
        Assembles the sub logs and uses the body pieces to combine it to
        a delivarable files

        :param sub_log_data: The data for the single sub log entries
        :return: The final file data
        """
        result = b""
        for element in self.body_pieces:
            if isinstance(element, str):  # log reference
                result += sub_log_data.get(element, b"")
            else:  # raw file data
                result += element
        return result
