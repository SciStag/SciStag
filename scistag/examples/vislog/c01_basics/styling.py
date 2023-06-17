"""
This demo shows several ways how you can style your text and content.

There are several ways to do so. As VisualLog is inspired by Markdown the most straight
forward way is to use text codes such as **bold** or *italic* to change the text style.

Alternatively and for more advanced, html-only styling you can though also use the
extensions .style and .align to style and align the text.
"""
from scistag.vislog import VisualLog, LogBuilder, cell


class StyleDemo(LogBuilder):
    @cell
    def text_styles(self):
        # Use markdown to make the text bold by enclosing it between double-asteriks
        self.md("**I am bold**")
        # Or use classic html
        self.html("<b>As am I</b>")
        # Following way all elements within the context are influenced by your style:
        with self.style("b"):
            self.add("I am bold too\n")
        # But
        self.style("B", "And I am extra-bold")
        self.add("**And me as well**\n", "md", br=True)

        with self.style("i"):
            self.title("Italic heading")
        self.style("#red", "Red").style("#green", "Green").style("#0000FF", "Blue").br()

        red = self.style.color("red")
        italic = self.style.italic()
        centered = self.align("center")
        combined = self.style("#blue") + italic + centered
        with self.style("_").align("right"):
            self.md("Underlined and right aligned")
        with red, italic, centered:
            self.text("Red italic and centered text")
        with combined:
            self.text("Blue italic and centered text")


if VisualLog.is_main():
    vl = VisualLog()
    vl.run_server(StyleDemo, auto_reload=True)
