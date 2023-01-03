from scistag.vislog import VisualLog, LogBuilder, cell
from scistag.vislog.widgets import LFileUpload


class ImageUploadDemo(LogBuilder):
    @cell
    def hello_world(self):
        self.log("Hello world")
        upload = LFileUpload(self)


if VisualLog.is_main():
    VisualLog().run_server(ImageUploadDemo)
