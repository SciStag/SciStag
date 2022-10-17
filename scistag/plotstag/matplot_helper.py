"""
Implements the matplot helper class which provides some basic wrapping functions
for integrating matplotlib
"""

import io

from scistag.imagestag import Image


class MPHelper:
    """
    Provides some basic helper functions for integrating matplotlib into
    scistag such as converting figures to Images.
    """

    @staticmethod
    def figure_to_png(figure, transparent=True) -> bytes:
        """
        Converts a figure to a png byte stream

        :param figure: The figure to be converted
        :param transparent: Defines if the figure shall be transparent
        :return: The byte stream
        """
        buffer = io.BytesIO()
        figure.savefig(buffer, format="png", transparent=transparent)
        return buffer.getvalue()

    @classmethod
    def figure_to_image(cls, figure, transparent=True) -> Image:
        """
        Converts a figure to an Image object

        :param figure: The figure to be converted
        :param transparent: Defines if the figure shall be transparent
        :return: The byte stream
        """
        image = Image(source=cls.figure_to_png(figure,
                                               transparent=transparent))
        return image
