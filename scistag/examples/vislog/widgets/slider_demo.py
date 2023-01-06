"""
Demo showing the usage of a slider widget
"""

from scistag.vislog import VisualLog, LogBuilder, cell


class SliderDemo(LogBuilder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.val = 0.3

    @cell(interval_s=0.01)
    def value(self):
        self.log(f"Current value: {self.val} ")

    @cell()
    def content(self):
        self.log("Hello world")

        def change_val():
            self.val = slider.value
            self.value.cell.invalidate()

        self.text("Contrast ", br=False)
        slider = self.widget.slider(
            self.val,
            0.1,
            2.0,
            stepping=0.1,
            on_change=change_val,
            show_value=True,
            vertical=False,
            value_max_digits=2,
            value_bold=True,
        )
        self.hr()

    @cell()
    def follow_up_cell(self):
        with self.align.left:
            self.text("Just a test")


if VisualLog.is_main():
    VisualLog().run_server(SliderDemo, auto_reload=True)
