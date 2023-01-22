from datetime import datetime

from scistag.vislog import VisualLog, cell, LogBuilder


class LiveLog(LogBuilder):
    @cell(interval_s=0.01, continuous=True)
    def dynamic_cell(self):
        self.title(str(datetime.now()))
        self.text(f"Total updates: {self.cache.inc('updates')}")

    @cell
    def widget_cell(self):
        self.br(2)

        def clicked():
            with self.event_log.cell:
                self.log("Button clicked")

        self.widget.button("Click me", clicked)
        self.widget.button("Clear", lambda: self.event_log.cell.clear())
        self.br(2)

    @cell(progressive=True, interval_s=0.1)
    def event_log(self):
        pass


if VisualLog.is_main():
    options = VisualLog.setup_options(title="Dynamic VisualLog")
    VisualLog(options).run_server(LiveLog)
