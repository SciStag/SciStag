"""
Tests the StyleContext extension
"""
from scistag.vislog import cell, LogBuilder, VisualLog
from .. import vl


def test_all_styles():
    """
    Executes the styling demo which makes use of all styling possibilities
    """

    class StyleBuilder(LogBuilder):
        @cell
        def log_style(self):
            self.test.checkpoint("vl_styling")
            self.style.help()
            self.test.assert_cp_diff("5753dd340c3a96d0e71edd9a7920378a")

    options = VisualLog.setup_options("disk")
    tl = VisualLog(fixed_session_id="", options=options)
    tl.run(builder=StyleBuilder)
