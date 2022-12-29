"""
Defines the class :class:`ElementContext` which helps storing
nested HTML components such as tables or divs in a document using Python
contexts.
"""

from __future__ import annotations

from scistag.vislog import LogBuilder


class ElementContext:
    """
    Defines a context which helps to dynamically fill advanced components
    such as HTML tables or divs with content.

    This is realized by asap storing their opening statements into the target
    document  such as `<table>` upon creation and automatically
    writing the closing statement such as `</table>` when either the object's
    context is left or the :meth:`close` method is called explicitly.
    """

    def __init__(self, builder: "LogBuilder", closing_code: {}):
        """
        :param builder: The builder object with which we write to the log
        """
        self.builder = builder
        """The build element which executes the page rendering"""
        self.page = builder.page_session
        """The target page in which the data is stored"""
        self.closing_code: dict = closing_code
        """The code which shall be appended when this context is closed"""
        self._closed = False
        """Defines if the context has been closed already"""

    def __enter__(self):
        return self

    def close(self):
        """
        Can be called to explicitly finish the current element
        """
        if self._closed:
            return
        self._closed = True
        from scistag.vislog import VisualLog

        for key, value in self.closing_code.items():
            if key in self.page.log_formats:
                from scistag.vislog.visual_log import HTML, MD, TXT

                if key == HTML:
                    self.page.write_html(value)
                elif key == MD:
                    self.page.write_md(value)
                elif key == TXT:
                    self.page.write_txt(value)
        self.page.handle_modified()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
