import numpy as np
from kivy.uix.image import Image
from kivy.graphics.texture import Texture


class AdvancedImage(Image):
    """
    Enhances the image class by the possibility to directly assign numpy arrays
    """

    def __init__(self, **kwargs):
        """
        Initializer
        :param kwargs:
        """
        super().__init__(**kwargs)
        self.image_texture = None
        self.auto_size = True  # Defines if the image gets automatically resized
        self.size_scaling = 1.0  # The size scaling factor
        self.previous_image = None

    def set_image_data(self, image_data: np.ndarray, bgr=False) -> None:
        """
        Sets the view's new image data
        :param image_data: The numpy image to set
        :param bgr: Defines if the data is passed in bgr order
        """
        buf = np.flip(image_data, 0).tostring()
        if self.previous_image is not None and len(self.previous_image.shape) != len(
            image_data.shape
        ):
            self.image_texture = None
        self.previous_image = image_data
        if (
            self.image_texture is not None
        ):  # Release old texture when the resolution changed
            if (
                self.image_texture.width != image_data.shape[1]
                or self.image_texture.height != image_data.shape[0]
            ):
                self.image_texture = None
        if len(image_data.shape) == 3:
            # create texture handle if required
            if self.image_texture is None:
                self.image_texture = Texture.create(
                    size=(image_data.shape[1], image_data.shape[0]), colorfmt="bgr"
                )
            # blit new data into the texture buffer
            color_format = "bgr" if bgr else "rgb"
            self.image_texture.blit_buffer(
                buf, colorfmt=color_format, bufferfmt="ubyte"
            )
        else:
            # create texture handle if required
            if self.image_texture is None:
                self.image_texture = Texture.create(
                    size=(image_data.shape[1], image_data.shape[0]),
                    colorfmt="luminance",
                )
            # blit new data into the texture buffer
            self.image_texture.blit_buffer(buf, colorfmt="luminance", bufferfmt="ubyte")
        # display image from the texture
        self.texture = self.image_texture
        self.canvas.ask_update()
        if self.auto_size:
            self.handle_auto_size()

    def handle_auto_size(self):
        """
        Automatically sets this view's size to it's image's size
        """
        if self.texture is not None:
            self.width = self.texture.width * self.size_scaling
            self.height = self.texture.height * self.size_scaling
