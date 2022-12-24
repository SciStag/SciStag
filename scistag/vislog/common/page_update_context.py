"""
Implements :class:`PageUpdateContext` which automatically triggers the updating of
a page after leaving a `with builder.begin_update()` context block.
"""
from scistag.vislog.sessions.page_session import PageSession


class PageUpdateContext:
    """
    Helper class to automatically finalize a synchronized update block of a
    VisualLogBuilder or PageSession. See :meth:`PageSession.begin_update`
    """

    def __init__(self, page_session: PageSession):
        """
        :param page_session: The page session of which the end_update method shall
            be called.
        """
        self.page_session = page_session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.page_session.end_update()
