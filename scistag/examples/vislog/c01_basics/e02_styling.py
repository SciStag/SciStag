"""
This demo shows several ways how you can style your text and content.

There are several ways to do so. As VisualLog is inspired by Markdown the most straight
forward way is to use text codes such as **bold** or *italic* to change the text style.

Alternatively and for more advanced, html-only styling you can though also use the
extensions .style and .align to style and align the text.
"""
from scistag.vislog import VisualLog, LogBuilder, cell, section


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

    @section("Basic Styling")
    def basic_styling(self):
        # Use markdown to make the text **bold** by enclosing it between
        # "double-asteriks"
        self.md("**I am bold**").br()
        self.html("Or use classic html such as <b>Bold</b>")
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

    @section("Combining style elements")
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

        self("It's of the ").style("h", "utmost importance ")("to build beautiful logs")

    @section("Reusing elements")
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

    @section("Custom css")
    def custom_css(self):
        # You can also register your own css style class using add_css. Use {{c}}
        # as placeholder for the class name
        style_class = self.style.add_css(
            ".{{C}} {color:red; font-weight: 950}", class_name="custom_style"
        )

        # pass the retrieved class name to style.css. do not hardcode the name if
        # you used add_css as it may be altered with a session id
        with self.style.css(css_class=style_class):
            self.text("Red ultra bold text")

        # of course you can also use css directly without declaring a class first
        with self.style.css("text-decoration: underline"):
            self.text("Underlined")

    @section("Fonts")
    def font_changing(self):
        # With the following approaches you can change font family, size and height
        with self.style.font(size=20):
            # Fonts can be selected by either calling style.font(family, size, weight)
            # or by selecting style.font.default to select the default font or any
            # of the common font families
            with self.style.font("Arial"):  # all elements in this block use Arial now
                self.text("Arial")
                with self.style.font(size="50px"):  # just increase size
                    self.text("... in large")
                self.style.font(None, 10)("... or small", br=True)  # just decrease size
            # Other default font families:
            with self.style.font.arial:
                self.text("Arial")
            with self.style.font.courier:
                self.text("Courier")
            with self.style.font.lucida:
                self.text("Lucida")
            with self.style.font.times:
                self.text("Times")
            with self.style.font.tahoma:
                self.text("Tahoma")
            with self.style.font.trebuchet:
                self.text("Trebuchet")
            with self.style.font.georgia:
                self.text("Georgia")
            with self.style.font.default:
                self.text("Default font")
            with self.style.font("sans-serif", size=35, weight=950):
                self.text("Tahoma")
            with self.style.font("sans-serif", size=35):
                self.text("Tahoma")

    @section("Defaults")
    def defaults(self):
        with self.style.font.courier:
            self.text("Courier")
            with self.style.font.default:
                self.text("Default font")
        with self.style.color("red"):
            self.text("Colored red")
            self.style.color.default.text("Using default color")
        with self.style.bg_color("black"):
            with self.style.color("blue"):
                self.text("Using black background")
        with self.style.bg_color.default:
            self.text("Using default background")

    @section("Overview")
    def overview(self):
        # Overview which evaluates every single style
        self.md("### Overview of all single character style codes")
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
        self.br()
        self.evaluate('self.style("h", "Highlighted")', -1, ml=True, sl=True)
        self.evaluate('self.style("E", "Error")', -1, ml=True, sl=True)
        self.evaluate('self.style("a", "ASCII\\nis\\nfun ;-)")', -1, ml=True, sl=True)
        self.md("### Property based style selection")
        self.evaluate('self.style.bold.add("Bold")', -1, ml=True, sl=True)
        self.evaluate('self.style.italic.add("Italic")', -1, ml=True, sl=True)
        self.evaluate('self.style.underlined.add("Underlined")', -1, ml=True, sl=True)
        self.md("### The different ways of color selection")
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
    vl.run_server(StyleDemo)
