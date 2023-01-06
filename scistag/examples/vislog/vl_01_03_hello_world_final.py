from scistag.vislog import VisualLog, cell, LogBuilder


class HelloWorldLog(LogBuilder):
    @cell
    def hello_world(self):
        vl = self
        with vl.align.center:
            vl.title("Hello world!")
            vl.emoji("*globe*", size=600).br()


if VisualLog.is_main():
    options = VisualLog.setup_options("disk&console")
    options.output.setup(formats={"html", "md", "txt"})
    VisualLog(title="First VisualLog", options=options).run(HelloWorldLog)
