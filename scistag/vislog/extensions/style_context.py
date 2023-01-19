"""
Defines :class:`StyleContext` which helps with inserting custom styles into the log
and temporarily modifying the style for parts of it.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Union, Callable

from scistag.vislog.extensions.builder_extension import BuilderExtension

if TYPE_CHECKING:
    from scistag.vislog.log_builder import LogBuilder


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
