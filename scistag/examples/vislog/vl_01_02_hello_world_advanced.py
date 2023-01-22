from scistag.vislog import VisualLog, cell, LogBuilder


@cell
def hello_world(vl: LogBuilder):
    vl.md.log_html_only = True
    with vl.align.center:
        vl.title("Hello world!")
        vl.emoji("*globe*", size=600).br()
        vl.log("Hello")
        vl.log("world")
        vl.log("how")


if VisualLog.is_main():
    options = VisualLog.setup_options("disk", title="First VisualLog")
    VisualLog(options=options).run()
