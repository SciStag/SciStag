from e02_styling import StyleDemo
from scistag.vislog import VisualLog

if VisualLog.is_main():
    options = VisualLog.setup_options("disk")
    options.output.setup(formats={"md", "txt", "html"})
    VisualLog(options=options).run(builder=StyleDemo)
