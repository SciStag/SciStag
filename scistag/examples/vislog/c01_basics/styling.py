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
    def head(self):
        with self.align.center:
            self.title("Text styling example")
        self.md(
            "This example shall give a small overview over the different kinds of "
            "styling possibilities to have with the LogBuilder's `.style` and "
            "`.align` extensions as well as with classical markdown or html styling"
        )

    @cell(section_name="Basic Styling")
    def basic_styling(self):
        # Use markdown to make the text **bold** by enclosing it between
        # "double-asteriks"
        self.md("**I am bold**").br()
        self.text("Or use classic html such as <b>Bold</b>")
        self.html("<b>Bold as well</b>").br()
        # By entering the element context such as via with self.style("b"):...
        # all elements within the context are affecting by the style:
        with self.style("b"):
            self.add("I am bold too\n")

        # If you just want to format a single element you can also pass the text
        # right after the style definition as second parameter
        self.style("B", "And I am extra-bold\n").br()
        # If the text has a special format such as html you can pass the type as
        # third parameter"
        self.style("#red", "**I combine styling and markdown**\n", "md")

    @cell(section_name="Combining style elements")
    def combining(self):
        # Of course you can also combine default elements such as titles and sub titles
        # with additional style flags:
        with self.style("i"):
            self.title("Italic heading")

        # if you do not enter the style context but pass the text directly the
        # LogBuilder object will be returned so you can chain multiple style (or other)
        # commands together
        self.style("#red", "Red").style("#green", "Green").style("#0000FF", "Blue").br()

        # Multiple ElementContext objects can be combined by joining both of their
        # context at once
        with self.style.underlined, self.align.right:
            self.md("Underlined and right aligned")

        # ElementContext objects such as from .align and .style can easily be added
        with self.style.bold + self.align.left + self.style("~_-o"):
            self.text("Bold, left aligned, underlined and marked as error")

        with self.align.center:
            self.text("Should be centered")
        self.text("Should be left")

    @cell(section_name="Reusing elements")
    def multi_use(self):
        # ElementContext objects can be used multiple times and also be combined
        # via the add operator.
        red = self.style.color("red")
        green = self.style.color("#00FF00")
        blue = self.style.color("blue")
        italic = self.style.italic
        centered = self.align("center")
        combined = self.style("#blue") + italic + centered
        with red, italic, centered:
            self.text("Red, italic and centered text")
        with combined:
            self.text("Blue, italic and centered text")
        # set shared background and bold style within the context
        with self.style.bg_color("black") + self.style.bold:
            # but switch the color element by element
            red.md("Red"), green.md("Green"), blue.md("Blue")

    @cell(section_name="Overview")
    def overview(self):
        # Overview which evaluates every single style
        self.md("### Overview of all single character style codes", br=False)
        self.evaluate('self.style("b", "Bold")', -1, ml=True, sl=True)
        self.evaluate('self.style("B", "Heavy")', -1, ml=True, sl=True)
        self.evaluate('self.style("u", "Underlined")', -1, ml=True, sl=True)
        self.evaluate('self.style("_", "Underlined too")', -1, ml=True, sl=True)
        self.evaluate('self.style("i", "Italic")', -1, ml=True, sl=True)
        self.br()
        self.evaluate('self.style("o", "Overlined")', -1, ml=True, sl=True)
        self.evaluate('self.style("-", "Stike-through")', -1, ml=True, sl=True)
        self.evaluate('self.style("^", "Superscript")', -1, ml=True, sl=True)
        self.evaluate('self.style(".", "Sub")', -1, ml=True, sl=True)
        self.br()
        self.evaluate('self.style("~_", "Wavy underline")', -1, ml=True, sl=True)
        self.evaluate('self.style("b", "Bold")', -1, ml=True, sl=True)
        self.evaluate('self.style("t", "Thin")', -1, ml=True, sl=True)
        self.evaluate('self.style("n", "normal")', -1, ml=True, sl=True)
        self.br()
        self.evaluate('self.style("m", "Marked")', -1, ml=True, sl=True)
        self.evaluate('self.style("d", "Deleted")', -1, ml=True, sl=True)
        self.evaluate('self.style("e", "Emphasized")', -1, ml=True, sl=True)
        self.evaluate('self.style("s", "Strong")', -1, ml=True, sl=True)
        self.evaluate('self.style("a", "ASCII\\nis\\nfun ;-)")', -1, ml=True, sl=True)
        self.md("### Property based style selection", br=False)
        self.evaluate('self.style.bold.add("Bold")', -1, ml=True, sl=True)
        self.evaluate('self.style.italic.add("Italic")', -1, ml=True, sl=True)
        self.evaluate('self.style.underlined.add("Underlined")', -1, ml=True, sl=True)
        self.br()
        self.md("### The different ways of color selection", br=False)
        self.evaluate('self.style.color("#00CC00").add("Green")', -1, ml=True, sl=True)
        self.evaluate('self.style.color("purple").add("Purple")', -1, ml=True, sl=True)
        self.evaluate('self.style("#fuchsia").add("Fuchsia")', -1, ml=True, sl=True)
        self.evaluate('self.style("#00CCCC").add("Cyan")', -1, ml=True, sl=True)
        self.evaluate('self.style.color("red").add("Red")', -1, ml=True, sl=True)
        self.evaluate(
            'self.style.bg_color("silver").add("Black")', -1, ml=True, sl=True
        )


if VisualLog.is_main():
    vl = VisualLog()
    vl.run_server(StyleDemo, auto_reload=True)
