"""
This demo shows how you can embed HTML and Markdown files into your log
and automatically let the document being rebuilt when ever you can any of
these files.
"""

from scistag.vislog import VisualLog, LogBuilder, cell


class MyPage(LogBuilder):
    """
    A basic landing page
    """

    @cell
    def markdown_demo(self):
        """
        Builds the page's content
        """
        self.md.embed("./e03_embedded_doc.md")


if VisualLog.is_main():
    options = VisualLog.setup_options()
    log = VisualLog(options=options).run_server(MyPage, auto_reload=True)
