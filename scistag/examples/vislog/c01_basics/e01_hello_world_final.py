"""
In this last hello world demo we
"""

from scistag.vislog import VisualLog, cell, LogBuilder


class HelloWorldLog(LogBuilder):
    @cell
    def hello_world(self):
        with self.align.center:
            self.title("Hello world!")
            self.emoji("*globe*", size=600).br()


if VisualLog.is_main():
    options = VisualLog.setup_options("disk&console", title="First VisualLog")
    options.output.setup(formats={"html", "md", "txt"}, console=True)
    vl = VisualLog(options=options)
    vl.run(HelloWorldLog)
    vl.default_page.show_info()
