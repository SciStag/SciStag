from scistag.vislog import VisualLog, cell, LogBuilder


@cell
def say_hello(vl: LogBuilder):
    vl.log("Hello world!")


if VisualLog.is_main():
    options = VisualLog.get_default_options()
    options.output.log_to_disk = True
    VisualLog(title="My first log", options=options).run()
