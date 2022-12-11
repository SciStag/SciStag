"""
Defines the class :class:`ElementContext` which helps storing
nested HTML components such as tables or divs in a document using Python
contexts.
"""

from __future__ import annotations

from scistag.vislog import VisualLogBuilder


class ElementContext:
    """
    Defines a context which helps to dynamically fill advanced components
    such as HTML tables or divs with content.

    This is realized by asap storing their opening statements into the target
    document  such as `<table>` upon creation and automatically
    writing the closing statement such as `</table>` when either the object's
    context is left or the :meth:`close` method is called explicitly.
    """

    def __init__(self, builder: "VisualLogBuilder", closing_code: {}):
        """
        :param builder: The builder object with which we write to the log
        """
        self.builder = builder
        self.closing_code: dict = closing_code
        self._closed = False

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

        log: VisualLog = self.builder.target_log
        for key, value in self.closing_code.items():
            if key in log.log_formats:
                from scistag.vislog.visual_log import HTML, MD, TXT

                if key == HTML:
                    log.write_html(value)
                elif key == MD:
                    log.write_md(value)
                elif key == TXT:
                    log.write_txt(value)
        log.handle_modified()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
