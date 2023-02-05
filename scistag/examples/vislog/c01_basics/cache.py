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
        self.widget.button("Click me", target="clicks")
        self.widget.button("Clear", lambda: self.event_log.cell.clear())
        self.br(2)

    @cell(progressive=True, interval_s=0.1, requires="clicks")
    def event_log(self):
        self.text(f'Button clicked {self.cache.get("clicks", 0)} times')


if VisualLog.is_main():
    options = VisualLog.setup_options(title="Dynamic VisualLog using a cache")
    VisualLog(options).run_server(LiveLog)
