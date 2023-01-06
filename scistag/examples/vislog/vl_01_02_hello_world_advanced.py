from scistag.vislog import VisualLog, cell, LogBuilder


@cell
def hello_world(vl: LogBuilder):
    vl.md.html_only = True
    with vl.align.center:
        vl.title("Hello world!")
        vl.emoji("*globe*", size=600).br()


if VisualLog.is_main():
    VisualLog(title="First VisualLog", options="disk").run()
