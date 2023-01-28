"""
A simple demo demonstrating how to use the LSelect widget which lets the user choose
a single value from a list of values.
"""

from scistag.vislog import LogBuilder, cell, section
from scistag.vislog.widgets import LSelect


class Demo(LogBuilder):
    @section("LSelect demo")
    def selector_demo(self):
        LSelect(
            self,
            html_style="color:blue; width:400px",
            elements=[
                {"text": "Select", "value": "First selected"},
                ("a value", "Second selected"),
                LSelect.Element(
                    text="from the list",
                    value="Third selected",
                    html_style="color:red",
                ),
                LSelect.Element(
                    text="But not me :)",
                    value="not selectable",
                    disabled=True,
                ),
            ],
            default_index=1,
            target="curSelectValue",
        )

    @cell(requires="curSelectValue")
    def show(self):
        self.sub(self["curSelectValue"])


Demo.run(as_service=True, auto_reload=True)
