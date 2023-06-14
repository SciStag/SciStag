from scistag.vislog import LogBuilder, cell, VisualLog
from scistag.vislog.options.extension_options import MERMAID_EXTENSION

demo_info = """This demo shows how to visualize a simple graph using Mermaid, a JavaScript solution
for graph rendering. See https://mermaid.js.org/ for more details about the
language itself.

To make use of it either install scistag with the [full] flag, e.g.
`pip install scistag[full]` or install chartstag separately.
"""


class SimpleGraph(LogBuilder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @cell
    def show_graph(self):
        self.title("Simple Graph")
        self.md(demo_info)
        # Add a graph directly by inserting the mermaid code using the .mmd function
        self.chart.mmd("graph TD\nX-->Y")
        # Embed a markdown file which contains
        self.md.embed("./simple_graph.md", watch=True)
        # Embed a graph directly from a file. Through the watch flag the chart
        # will automatically get updated when ever you change the file.
        self.sub("A graph embedded from a Mermaid file")
        self.chart.embed("./sequence_diagram.mmd", watch=True)


if VisualLog.is_main():
    options = VisualLog.setup_options()
    # you need to enable the mermaid extension and "chartstag" needs to be installed
    options.extensions.add(MERMAID_EXTENSION)
    SimpleGraph.run(as_service=True, options=options, auto_reload=True)
