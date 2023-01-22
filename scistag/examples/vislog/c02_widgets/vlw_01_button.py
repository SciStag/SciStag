"""
This demo shows how to add a simple button control to the log and update content
whenever the button was clicked.
"""

from scistag.vislog import VisualLog, LogBuilder, cell


class ButtonLog(LogBuilder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.counter = 0

    @cell
    def content(self):
        def inc_counter():
            self.counter += 1
            # You can access a cell produced via the cell decorator via
            # the function_name.cell or self.cell["functionName"]
            # .invalidate requests a rebuild of that specific cell.
            self.content.cell.invalidate()
            # self.cell["content"].invalidate()  # were also fine

        self.title("A simple button click demo")
        self.md(f"**You clicked the button {self.counter} times**").br()
        # A button which increases the counter and rebuilds this cell
        self.widget.button(
            "Click me to increase the counter", on_click=inc_counter,
            name="inc_button"
        )
        self.br().br()
        # A button which triggers the progressive content cell to extend itself
        self.widget.button(
            "Click me to add an entry to the progress list",
            on_click=lambda: self.add_progressive_content(),
            name="add_button"
        )
        self.br(2)
        # A button which clears the progress list
        self.widget.button(
            "Clear the progress list",
            on_click=lambda: self.progressive_content.cell.clear(),
            name="clear_button"
        )
        self.br(2).hr().br()

    def add_progressive_content(self):
        with self.progressive_content.cell:
            self.log("A dynamically added value")

    @cell(interval_s=0.1, progressive=True)
    def progressive_content(self):
        self.log("A log entry in a progressive cell")


if VisualLog.is_main():
    VisualLog().run_server(builder=ButtonLog)
