from scistag.imagestag.image_filter import ImageFilter, Image, IMAGE_FILTER_IMAGE


class GrayscaleFilter(ImageFilter):
    """
    Converts the input image to grayscale
    """

    def __init__(self):
        """
        Initializer
        """
        super(GrayscaleFilter, self).__init__()
        self.name = "grayscale"

    def _apply_filter(self, input_data: dict) -> dict:
        image: Image = input_data[IMAGE_FILTER_IMAGE]
        return {
            IMAGE_FILTER_IMAGE: Image(
                image.get_pixels_gray(), framework=image.framework
            )
        }
