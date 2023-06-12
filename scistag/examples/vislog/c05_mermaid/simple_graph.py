"""
Shows how to create a simple graph
"""
from scistag.vislog import LogBuilder, cell, VisualLog
from scistag.vislog.options.extension_options import MERMAID_EXTENSION


class SimpleGraph(LogBuilder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @cell
    def show_graph(self):
        self.title("Simple Graph")
        self.md.embed("./simple_graph.md", watch=True)
        self.chart.mmd("graph TD\nX-->Y")


if VisualLog.is_main():
    options = VisualLog.setup_options()
    options.extensions.add(MERMAID_EXTENSION)
    SimpleGraph.run(as_service=True, options=options)
