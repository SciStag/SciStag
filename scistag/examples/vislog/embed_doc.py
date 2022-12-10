"""
This demo shows how you can embed HTML and Markdown files into your log
and automatically let the document being rebuilt when ever you can any of
these files.
"""

from scistag.vislog import VisualLog, VisualLogBuilder


class MyPage(VisualLogBuilder):
    """
    A basic landing page
    """

    def build(self):
        """
        Builds the page's content
        """
        self.md.embed("./embed_doc.md")
        self.md("# Test")


if VisualLog.is_main():
    log = VisualLog(auto_reload=MyPage, start_browser=True)
