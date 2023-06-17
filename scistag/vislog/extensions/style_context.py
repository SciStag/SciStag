"""
Defines :class:`StyleContext` which helps with inserting custom styles into the log
and temporarily modifying the style for parts of it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union, Callable

from scistag.vislog.common.element_context import ElementContext
from scistag.vislog.extensions.builder_extension import BuilderExtension
from scistag.webstag.mime_types import MIMETYPE_ASCII

if TYPE_CHECKING:
    from scistag.vislog.log_builder import LogBuilder, LogableContent


class StyleContext(BuilderExtension):
    """
    Helper class for inserting custom styles into the log and temporarily modifying
    the style for the current cell or cell region.
    """

    def __init__(self, builder: "LogBuilder"):
        """
        :param builder: The builder object with which we write to the log
        """
        super().__init__(builder)

    def css(
        self,
        code: str,
        class_name: str | None = None,
        insert: bool = True,
    ) -> str:
        """
        Inserts CSS code (Cascading Style Sheet) into the output log

        :param code: The code to be inserted.

            All occurrences of {{C}} will be replaced with the new class name,
            all occurrences of {{PC}} will be replaced with the parent class name
        :param class_name: The name of the class to be reserved. May be slightly altered
            with a number to prevent collisions, e.g. my_class -> my_class_01.

            If you start the name with an @-sign the name will be enforced and the
            style written again, even if the name might already exist.
        :param insert: Defines if the CSS code shall be inserted asap
        :return: The class name
        """
        class_name = (
            class_name[1:]
            if class_name is not None and class_name.startswith("@")
            else self.page_session.reserve_unique_name(class_name)
            if class_name is not None
            else None
        )
        if "{{C}}" in code:
            if class_name is None:
                class_name = self.page_session.reserve_unique_name("custom_style")
            code = code.replace("{{C}}", class_name)
        if insert:
            self.builder.html(f"<style>{code}</style>")
        return class_name

    def ensure_css_class(self, name_or_code: str, class_category: str | None = None):
        """
        Ensures that the passed parameter is a css class.

        If instead of a class CSS code is passed a css class will automatically be
        created with a generic name and all occurrences of {{C}} in the code will be
        replaced with this name.

        :param name_or_code: The CSS name to assign to the object or the code of the
            new CSS style to generate.
        :param class_category: Defines how the CSS class name shall begin in case it
            needs to be created.
        :return: Either name if it already was a valid class name, otherwise the
            name of the newly created class.
        """
        if "{" not in name_or_code:
            return name_or_code
        return self.css(code=name_or_code, class_name=class_category)

    def __call__(
        self,
        style: str,
        content: LogableContent | None = None,
        mimetype: str | None = None,
    ) -> ElementContext | LogBuilder:
        """
        Creates a style content and returns it

        :param style: The style(s) to be applied defined as a semicolon separated string
            of the following style configuration elements types:
            * Single character sequence - A single string (w/o semicolons) in which
              each style flag is represented by a single character:
                * "b" - Bold
                * "B" - Ultra bold
                * "t" - Thin
                * "n" - Normal
                * "S" - Strong
                * "s" - Small
                * "i" - Italic
                * "e" - Emphasize
                * "d" - Deleted
                * "m" - Mark text
                * "_" or "u" - Underlined
                * "-" - Strike-through
                * "‾" or "o" - Overline
                * "~" - Waved marker with the default error color
                * "^" - Superscript vertical text alignment
                * "." - Subscript vertical text alignment

              Example: with logbuilder.style("ib_"):... would result in italic, bold
              underlined text.
            * Color: Either RGB values in the HTML-like format #RRGGBB (all uppercase)
                such as style("#00FF00") or as well a # followed by the
                color's name (all lower case) such as style("#green")
        :param content: If provided the content will be added via the "add" method
            within the new style's context. This allows writing more compact code
            as the content does not need to be entered.

            Example: logbuilder.add("x").style("^", "2") - will add x squared to the
            log.
        :param mimetype: Defines the mimetype (such as "md" for markdown) to be passed
            to the **add** call. Only has effect if **content** is provided.
        :return: The context element if no content was provided. Otherwise
            the LogBuilder object.
        """
        md_html = self.builder.md.log_html_only
        md = []  # code to be inserted in front of md content
        md_closing = []  # code to be inserted after md content
        html = []  # code to be inserted in front of html content
        html_closing = []  # code to be inserted after html content
        css_style = []  # css style elements to be concatenated
        text_deco = []  # text-decoration
        sub_styles = style.split(";")
        flag_set = set()
        for cs_element in sub_styles:
            if cs_element.startswith("#") and len(cs_element) > 1:  # color
                rest = cs_element[1:]
                if len(rest) == 6 and rest.upper() == rest:
                    rest = "#" + rest
                css_style += [f"color:{rest}"]
                continue
            flag_set = flag_set.union(set(cs_element))
        self._evaluate_flags(
            css_style, flag_set, html, html_closing, md, md_closing, text_deco
        )
        if len(text_deco):
            css_style += [f"text-decoration: {' '.join(text_deco)}"]
        if len(css_style) > 0:
            html += [f'<span style="{";".join(css_style)}">']
            html_closing += ["</span>"]
        j_html = "".join(html)
        j_html_closing = "".join(html_closing)
        j_md = "".join(md)
        j_md_closing = "".join(md_closing)
        context = ElementContext(
            builder=self.builder,
            opening_code={"html": j_html, "md": j_html if md_html else j_md},
            closing_code={
                "html": j_html_closing,
                "md": j_html_closing if md_html else j_md_closing,
            },
        )
        if content is not None:
            context.add(content, mimetype=mimetype)
            return self.builder
        return context

    def bold(self) -> ElementContext:
        """
        Returns a bold context within which all text is written bold

        :return: The context
        """
        md_html = self.builder.md.log_html_only
        html = '<span style="font-weight:bold">'
        html_closing = "</span>"
        return ElementContext(
            builder=self.builder,
            opening_code={
                "html": html,
                "md": html if md_html else "**",
            },
            closing_code={
                "html": html_closing,
                "md": html_closing if md_html else "**",
            },
        )

    def italic(self) -> ElementContext:
        """
        Returns an italic context within which all text is written italic

        :return: The context
        """
        md_html = self.builder.md.log_html_only
        html = '<span style="font-style:italic">'
        html_closing = "</span>"
        return ElementContext(
            builder=self.builder,
            opening_code={
                "html": html,
                "md": html if md_html else "*",
            },
            closing_code={
                "html": html_closing,
                "md": html_closing if md_html else "*",
            },
        )

    def underlined(self) -> ElementContext:
        """
        Returns an underlined context within which all text is written italic

        :return: The context
        """
        md_html = self.builder.md.log_html_only
        html = '<span style="text-decoration: underlined">'
        html_closing = "</span>"
        return ElementContext(
            builder=self.builder,
            opening_code={
                "html": html,
                "md": html if md_html else "",
            },
            closing_code={
                "html": html_closing,
                "md": html_closing if md_html else "",
            },
        )

    def color(self, name: str) -> ElementContext:
        """
        Returns a color context within which all text is written italic

        :param name: The color's name or hex code such as "red" or "#FF0000"
        :return: The context
        """
        md_html = self.builder.md.log_html_only
        html = f'<span style="color: {name}">'
        html_closing = "</span>"
        return ElementContext(
            builder=self.builder,
            opening_code={
                "html": html,
                "md": html if md_html else "",
            },
            closing_code={
                "html": html_closing,
                "md": html_closing if md_html else "",
            },
        )

    @staticmethod
    def _evaluate_flags(
        css_style, flag_set, html, html_closing, md, md_closing, text_deco
    ):
        """Evaluates character style flags in flag_set and adds the required tags
        to the markdown, html and css code to apply them"""
        if "b" in flag_set:  # bold
            css_style += ["font-weight:bold"]
            md += ["**"]
            md_closing += ["**"]
        if "B" in flag_set:  # ultra bold
            css_style += ["font-weight:950"]
            md += ["**"]
            md_closing += ["**"]
        if "n" in flag_set:  # thin
            css_style += ["font-weight:400"]
            md += ["**"]
            md_closing += ["**"]
        if "t" in flag_set:  # thin
            css_style += ["font-weight:200"]
            md += ["**"]
            md_closing += ["**"]
        if "i" in flag_set:  # italic
            css_style += ["font-style:italic"]
            md += ["*"]
            md_closing += ["*"]
        if "e" in flag_set:  # emphasized
            html += ["<em>"]
            html_closing += ["</em>"]
        if "d" in flag_set:  # deleted
            html += ["<del>"]
            html_closing += ["</del>"]
        if "s" in flag_set:  # strong
            html += ["<strong>"]
            html_closing += ["</strong>"]
        if "a" in flag_set:
            css_style += [
                "display:inline; font-family:monospace; font-size:12pt; white-space:pre"
            ]
        if "-" in flag_set:  # line-through
            text_deco += ["line-through"]
        if "_" in flag_set or "u" in flag_set:  # underline
            text_deco += ["underline"]
        if "‾" in flag_set or "o" in flag_set:
            text_deco += ["overline"]  # overline
        if "~" in flag_set:
            text_deco += ["red underline overline wavy"]
        if "^" in flag_set:  # superscript
            html += ["<sup>"]
            html_closing += ["</sup>"]
        if "." in flag_set:  # subscript
            html += ["<sub>"]
            html_closing += ["</sub>"]

    def help(self):
        vl = self.builder
        vl.title("Style Context")
        vl = self.builder
        vl.md(
            """The StyleContext class allows you to control the visual style of the
elements which are added within the style's context such as **text color**,
**font, font-weight** or decorations such as **underlining**.

The most compact way to modify the style is via the `call` function of the
StyleContext in which you pass all style parameters as a single string in
the first parameter and  and passing the content as second parameter such as"""
        )
        vl.sub("Example")
        vl.evaluate(
            'vl.add("This text is not bold ").style("b", "But this one is!")',
            br=True,
            log_code=True,
        )
        vl.md(
            """
        * "b" - Bold
        * "i" - Italic
        * "_" or "u" - Underlined
        * "-" - Strike-through
        * "‾" or "o" - Overline
        * "~" - Waved marker with the default error color
        * "^" - Superscript vertical text alignment
        * "." - Subscript vertical text alignment"""
        )
        vl.evaluate(
            'with vl.style("bi"):\n\tvl.text("Styled text")', br=True, log_code=True
        )
