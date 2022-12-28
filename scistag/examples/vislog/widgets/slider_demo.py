"""
Demo showing the usage of a slider widget
"""

from scistag.vislog import VisualLog, VisualLogBuilder, cell


class SliderDemo(VisualLogBuilder):
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

        style = self.options.style.slider.copy()
        style.show_value = True
        style.vertical = False
        style.value_max_digits = 2
        style.value_bold = True
        self.text("Contrast ", br=False)
        slider = self.widget.slider(
            self.val, 0.1, 2.0, stepping=0.1, on_change=change_val, style=style
        )
        self.hr()


if VisualLog.is_main():
    VisualLog(refresh_time_s=0.001).run_server(SliderDemo)
