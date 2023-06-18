"""
Defines :class:`StyleContext` which helps with inserting custom styles into the log
and temporarily modifying the style for parts of it.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Union

from scistag.filestag import FileStag
from scistag.vislog.common.element_context import ElementContext
from scistag.vislog.extensions.builder_extension import BuilderExtension
from scistag.vislog.extensions.font_style_context import FontStyleContext
from scistag.vislog.extensions.color_style_context import ColorStyleContext

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
        self.font = FontStyleContext(builder)
        "The font selection extension"
        self.color = ColorStyleContext(self.builder)
        "Color styling context"
        self.bg_color = ColorStyleContext(self.builder, background=True)
        "Background color styling context"

    def add_css(
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
        return self.add_css(code=name_or_code, class_name=class_category)

    def css(self, css: str = "", css_class: str | None = None) -> ElementContext:
        """
        Returns an element context defining a custom span style

        :param css: The code, such as "font-weight: 250"
        :param css_class: The class to use for the span
        :return: The element context
        """
        md_html = self.builder.md.log_html_only
        class_str = "" if css_class is None else f' class="{css_class}"'
        html = f'<span style="{css}"{class_str}>'
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

    def __call__(
        self,
        style: str,
        content: LogableContent | None = None,
        mimetype: str | None = None,
    ) -> Union[ElementContext, "LogBuilder"]:
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
                * "h" - Highlight text
                * "E" - Error (highlight error)
                * "_" or "u" - Underlined
                * "-" - Strike-through
                * "‾" or "o" - Overline
                * "~" - Waved marker with the default error color. The wave marker
                  always needs to be combined with either underline, overline or
                  line-through.
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

    @property
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

    @property
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

    @property
    def underlined(self) -> ElementContext:
        """
        Returns an underlined context within which all text is written italic

        :return: The context
        """
        md_html = self.builder.md.log_html_only
        html = '<span style="text-decoration: underline">'
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
        if "h" in flag_set:  # highlighted
            html += ["<span class='vl_highlighted'>"]
            html_closing += ["</span>"]
        if "E" in flag_set:  # error
            html += ["<span class='vl_error'>"]
            html_closing += ["</span>"]
        if "m" in flag_set:  # marked
            html += ["<mark>"]
            html_closing += ["</mark>"]
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
        StyleContext._handle_line_flags(flag_set, text_deco)
        if "^" in flag_set:  # superscript
            html += ["<sup>"]
            html_closing += ["</sup>"]
        if "." in flag_set:  # subscript
            html += ["<sub>"]
            html_closing += ["</sub>"]

    @staticmethod
    def _handle_line_flags(flag_set, text_deco):
        """
        Handles the line flags for under, over and line through, wavy or normal

        :param flag_set: The flag set
        :param text_deco: The text decoration to which the effects shall be added
        """
        if "~" in flag_set:
            line_deco = "red wavy"
            org_len = len(line_deco)
            if "-" in flag_set:  # line-through
                line_deco += " line-through"
            if "_" in flag_set or "u" in flag_set:  # underline
                line_deco += " underline"
            if "‾" in flag_set or "o" in flag_set:
                line_deco += " overline"
            if len(line_deco) == org_len:
                raise ValueError(
                    "You have to be combine the style ~ with one or more "
                    "underline, overline or line-through flags such"
                    'as "~_".'
                )
            text_deco += [line_deco]  # overline
        else:
            if "-" in flag_set:  # line-through
                text_deco += [f"line-through"]
            if "_" in flag_set or "u" in flag_set:  # underline
                text_deco += [f"underline"]
            if "‾" in flag_set or "o" in flag_set:
                text_deco += [f"overline"]  # overline

    def help(self):
        """
        Displays help about this element in the current log
        """
        from scistag.examples.vislog.c01_basics.styling import StyleDemo

        source = FileStag.load_text(inspect.getsourcefile(StyleDemo), crlf=False)
        result = StyleDemo.run(
            filetype="html", nested=True, fixed_session_id="style_demo"
        )
        self.builder.text(
            "Below you can find the output and source code of the styling example."
        ).hr()
        self.builder.add_html(result)
        self.builder.br()
        self.builder.code(source)
