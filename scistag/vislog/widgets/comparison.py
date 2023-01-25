"""
The LComparator widget allows the comparison of two content elements such as images
"""
from __future__ import annotations

from enum import IntEnum
from typing import List

from scistag.imagestag import Image
from scistag.vislog import LogBuilder, HTML
from scistag.vislog.widgets.log_widget import LWidget


class LComparison(LWidget):
    """
    The comparison widget allows the comparison of loggable elements such as images
    in form of a split view for example or adjustable opacities of the different layers.
    """

    class Style(IntEnum):
        HOR_SPLIT = 1
        """Splits the two content areas horizontally and lets the user slide between the
        front and the background element to the left and right"""

    def __init__(
        self,
        builder: LogBuilder,
        content: List[Image],
        style: Style,
        name: str = "Comparison",
        insert: bool = True,
    ):
        """
        :param builder: The builder
        :param content: The elements we want to compare. If only one object is
            passed the content will be logged via `add` as fallback.
        :param style: The style in which the comparison object is visualized
        :param name: The widget's name (optional)
        :param insert: Defines if the widget shall asap be inserted into the log
        """
        super().__init__(builder=builder, name=name, is_view=True)
        self.temp_content: List | None = content
        """Temporary content storage, is cleared as soon as it's not required anymore"""
        self._content_size = None
        if len(content) > 0 and isinstance(content[0], Image):
            self._content_size = content[0].size
        self.style = style
        "Defines the comparison widget's visual style"
        if self.style != self.Style.HOR_SPLIT:
            raise ValueError("Unsupported style")
        if insert:
            self.insert_into_page()

    def write(self):
        if len(self.temp_content) == 0:
            return
        if len(self.temp_content) == 1:
            if isinstance(self.temp_content[0], Image):
                self.builder.add(self.temp_content[0])
                self.temp_content = None
                return
        if len(self.temp_content) != 2 or not isinstance(self.temp_content[1], Image):
            raise ValueError(
                "At the moment only the comparison of two images is " "supported"
            )
        object_code = []
        for element in self.temp_content:
            with self.builder.snippet as rc:
                self.builder.image(element, scaling=1.0)
            object_code.append(rc.recording.data)

        replacements = {
            "350px": f"{self._content_size[0]}px",
            "250px": f"{self._content_size[1]}px",
        }
        html = self.render(
            "{{TEMPLATES}}/extensions/comparator/vl_comparator.html",
            replacements=replacements,
        )
        parts = html.split("CONTENT")
        self.page_session.write_html(parts[0])
        self.page_session.write_html(object_code[0][HTML])
        self.page_session.write_html(parts[1])
        self.page_session.write_html(object_code[1][HTML])
        self.page_session.write_html(parts[2])
        self.builder.add_txt("<<Comparison>>", targets="*")
