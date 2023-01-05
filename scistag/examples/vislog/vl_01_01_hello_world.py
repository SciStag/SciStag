from scistag.vislog import VisualLog, cell, LogBuilder


@cell
def say_hello(vl: LogBuilder):
    vl.md.html_only = True
    with vl.align.text_center:
        vl.title("Hello world!")
        vl.emoji("*globe*", size=800).br()


if VisualLog.is_main():
    options = VisualLog.get_default_options(log_to_disk=True, formats={"html", "md", "txt"})
    options.output.log_to_stdout = True
    VisualLog(title="My first log", options=options).run()
