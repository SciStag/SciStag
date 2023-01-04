from scistag.imagestag import Image
from scistag.vislog import VisualLog, LogBuilder, cell
from scistag.vislog.widgets import LFileUpload, LFileUploadEvent


class ImageUploadDemo(LogBuilder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.images = []
        self.errors = []

    @cell
    def hello_world(self):
        def handle_upload(event: LFileUploadEvent):
            self.images = []
            self.errors = []
            for cur_file in event.files:
                try:
                    image = Image(cur_file.data)
                except ValueError:
                    self.errors.append(f"{cur_file.filename} is invalid")
                    continue
                resize_image = image.resized_ext(max_size=512)
                self.images.append((image, resize_image, cur_file))
            self.image_cell.invalidate()

        with self.align.left:
            LFileUpload(self, on_upload=handle_upload)
        with self.align.right:
            self.text("Some text")
        with self.align.center:
            self.text("Some text")
        with self.align.left:
            self.text("Some text")

    @cell
    def image_cell(self):
        for error in self.errors:
            self.log.error(error)
        if len(self.images) == 0:
            return
        with self.table.begin(header=True, index=False) as table:
            table.add_row(["Filename", "Image", "Dimensions"], mimetype="md")
            for index, cur_image in enumerate(self.images):
                org_image, image, attachment = cur_image
                resolution = f"{org_image.size[0]}x{org_image.size[1]} pixels"
                table.add_row(
                    [
                        attachment.filename,
                        cur_image[1],
                        resolution,
                    ]
                )


if VisualLog.is_main():
    VisualLog().run_server(ImageUploadDemo)
