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
            self.test.assert_cp_diff("9f3cb2dd438670dd171d742bceeac79f")

    options = VisualLog.setup_options("disk")
    tl = VisualLog(fixed_session_id="", options=options)
    tl.run(builder=StyleBuilder)
