from scistag.vislog import VisualLog, LogBuilder, cell


class StyleDemo(LogBuilder):
    @cell
    def text_styles(self):
        self.style("color=red").add("X", br=False)
        self.add("Y", br=True)
        self.add("X").style("^", "2")
        self.align()
        self.style.help()


if VisualLog.is_main():
    vl = VisualLog()
    vl.run_server(StyleDemo, auto_reload=True)
