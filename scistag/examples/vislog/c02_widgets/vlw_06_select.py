"""
A simple demo demonstrating how to use the LSelect widget which lets the user choose
a single value from a list of values.
"""

from scistag.vislog import LogBuilder, cell, section
from scistag.vislog.widgets import LSelect


class Demo(LogBuilder):
    @section("LSelect demo")
    def selector_demo(self):
        self.md(
            """
        The **LSelect** class defines a drop-down box widget, also known as 
        combobox or select element from which the user can select a value.
        
        It has the following **required parameters**:
        
        ### elements - list[str|tuple|dict|LSelect.Element)
        
        **elements** defines the single entries from which the user can
        choose. Each element can be one of the following types:
        
        * Just a **str**ing - the string becomes the caption and the value has to be
            obtained by the element's index
        * A **dict** containing the properties **text** and **value** defining the 
          value shown and the value which will be passed to all on_change events, passed
          into the target variable
        * A **tuple** of two strings defining the text and the value
        * An **LSelect.Element** object containing all information
        
        ### Common parameters
        
        * **target** - The cache entry in which the current (and initial) value shall
            be stored.
        * **on_change**: The callback to be called when the value changed
        * **default_index**: The initially selected element (if not already defined via
            a LSelect element's **default** flag)
        """
        )
        elements = [
            "An element",
            {"text": "Select", "value": "First selected"},
            ("a value", "Second selected"),
            LSelect.Element(
                text="from the list", value="Third selected", html_style="color:red"
            ),
            LSelect.Element(
                text="But not me :)",
                value="not_sel",
                disabled=True,
            ),
        ]

        LSelect(
            self,
            html_style="font-weight:bold; width:400px",
            elements=elements,
            default_index=1,
            target="curSelectValue",
        )

    @cell(requires="curSelectValue")
    def show(self):
        self.sub(self["curSelectValue"])


Demo.run(as_service=True, auto_reload=True)
