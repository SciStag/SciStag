from scistag.imagestag import Image
from scistag.vislog import VisualLog, LogBuilder, cell, data, once, section
from scistag.vislog.widgets import LFileUpload, LFileUploadEvent


class ImageUploadDemo(LogBuilder):
    @cell
    def upload_view(self):
        self.md(
            """
        # Simple Image Upload
        
        This demo shows how to use the **FileUpload** widget to receive and process
        custom files the user provided. 
        
        This can be images or for example be
        
        * Image files
        * CSV files, Excel tables or other database formats
        * Text documents
        
        ## Overview
        
        * The cell **upload_view** creates at the upload widget and defines that only
          image files are accepted and that the **process_image_files** method shall
          be called to process them.
        * Once the user provides files the **process_image_files** method is called.
            * All successfully processed images will be stored in the data cache under
            the name **"images"**
            * All errors are stored in **"errors"**
        * Once "images" has content the **image_view** is displayed and shows all
          images
        * In case of an error, e.g. a non-image file uploaded also the cell
        **error_view** will be displayed, showing the **"errors""**' occurred.           
        """
        )
        self.hr()
        with self.align.left:
            LFileUpload(
                self,
                on_upload=self.process_image_files,
                max_file_count=20,
                gallery_items=9,
                max_upload_size=50 * 1024 * 1024,
                types="image/*",
            )

    def process_image_files(self, event: LFileUploadEvent):
        # create and clear "images" list
        images = self["images"] = []
        # create and clear "errors" list
        errors = self["errors"] = []
        for cur_file in event.files:  # process all files
            try:
                image = Image(cur_file.data)
                resized = image.resized_ext(max_size=(512, 512))
                images.append((image, resized, cur_file))
            except ValueError:
                errors.append(f"Error loading image {cur_file.filename}")

    @section("Processed images", requires="images>0")
    def image_view(self):
        with self.table.begin(header=True) as table:  # table with header
            # define header row
            table.add_row(["Filename", "Image", "Dimensions"], mimetype="md")
            # add content row
            for index, cur_image in enumerate(self["images"]):
                org_image, image, attachment = cur_image
                resolution = f"{org_image.size[0]}x{org_image.size[1]} pixels"
                with table.add_row() as row:
                    row.add(attachment.filename)
                    row.add(cur_image[1])
                    row.add(resolution)

    @section("Errors", requires="errors>0")
    def error_view(self):
        for cur_error in self["errors"]:
            self.log.error(cur_error)


if VisualLog.is_main():
    VisualLog().run_server(ImageUploadDemo)
