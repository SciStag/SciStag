from scistag.vislog import VisualLog, LogBuilder, cell


class ImageUploadDemo(LogBuilder):
    @cell
    def hello_world(self):
        self.log("Hello world")


if VisualLog.is_main():
    VisualLog().run_server(ImageUploadDemo)
