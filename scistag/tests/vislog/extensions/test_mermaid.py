from scistag.filestag import FilePath
from scistag.vislog import LogBuilder, VisualLog, cell
from scistag.vislog.options.extension_options import MERMAID_EXTENSION


class MmdLog(LogBuilder):
    @cell
    def add_mmd(self):
        self.test.checkpoint("Mermaid")
        # add a dynamic graph
        self.chart.mmd("graph TB\nA-->B")
        # embed a mermaid file
        path = FilePath.absolute_comb("test_mermaid_sample.mmd")
        self.chart.embed(path)
        # embed a markdown file
        path = FilePath.absolute_comb("test_mermaid_sample.md")
        self.md.embed(path)
        self.test.assert_cp_diff("d2f9f613f752145947164fa480955261")


def test_mermaid():
    """
    Tests the mermaid functionality
    """
    options = VisualLog.setup_options("disk")
    options.output.target_dir = FilePath.dirname(__file__) + "/logs/mermaid"
    # you need to enable the mermaid extension and "chartstag" needs to be installed
    options.extensions.add(MERMAID_EXTENSION)
    MmdLog.run(options=options, fixed_session_id="mermaid")
