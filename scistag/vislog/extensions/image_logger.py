"""
Defines the class :class:`ImageLogger` which helps storing images in
a VisualLog.
"""

from __future__ import annotations

import base64
from typing import Optional, TYPE_CHECKING
import numpy as np
from filetype import filetype

from scistag.common import SystemInfo
from scistag.filestag import FilePath, FileStag
from scistag.imagestag import Image, Canvas
from scistag.imagestag.ascii_image import AsciiImageMethod
from scistag.vislog import TXT, CONSOLE
from scistag.vislog.extensions.builder_extension import BuilderExtension

if TYPE_CHECKING:
    from scistag.imagestag import PixelFormat
    from scistag.vislog.visual_log import VisualLog
    from scistag.vislog.log_builder import LogBuilder

MAXIMUM_IMAGE_WIDTH = 8096
"""
The absolute maximum width of an image
"""

MAX_SIZE_ERROR = (
    f"The maximum image width is {MAXIMUM_IMAGE_WIDTH} pixels. "
    f"Note that a max_columns passed as floating point is "
    f"handled as scaling factor relative to the log's maximum"
    f"width."
)


class ImageLogger(BuilderExtension):
    """
    Helper class for storing images in a VisualLog
    """

    def __init__(self, builder: "LogBuilder"):
        """
        :param builder: The log builder object we are logging with
        """
        super().__init__(builder)
        self.show = self.__call__

    def __call__(
        self,
        source: Image | Canvas | str | bytes | np.ndarray,
        name: str | None = None,
        alt: str | None = None,
        title: str | None = None,
        pixel_format: Optional["PixelFormat"] | str | None = None,
        download: bool | None = None,
        scaling: float = 1.0,
        max_width: int | float | None = None,
        filetype: str | tuple[str, int] | None = None,
        optical_scaling: float = 1.0,
        br=True,
        text: str | None = None,
    ):
        """
        Adds an image to the log.

        :param name: The name of the image under which it shall be stored
            on disk (in case write_to_disk is enabled).
        :param source: The data object, e.g. an scitag.imagestag.Image, a
            numpy array, an URL or a FileStag compatible link.
        :param alt: An alternative text if no image can be displayed
        :param title: The image's title (which will be displayed if the mouse hovers
            above it)
        :param pixel_format: The pixel format (in case the image is passed
            as numpy array). By default gray will be used for single channel,
            RGB for triple band and RGBA for quad band sources.
        :param download: Defines if an image shall be downloaded.
            By default True if embed_images if set to True in the options,
            false otherwise.
        :param scaling: The factor by which the image shall be scaled
        :param max_width: Defines if the image shall be scaled to a given size.

            Possible values
            - True = Scale to the log's max_fig_size.
            - float = Scale the image to the defined percentual size of the
                max_fig_size, 1.0 = max_fig_size

        :param filetype: The image format, with our without quality grade
            e.g. "jpg" or ("jpg", 90).

            Has no effect if the image was already as bytes stream.
        :param optical_scaling: Defines the factor with which the image shall
            be visualized on the html page without really rescaling the image
            itself and thus giving the possibility to zoom in the browser.
        :param br: Defines if a linebreak shall be inserted after
            the image.
        """
        if not self.builder.options.style.image.log_images:
            return
        if download is None:
            download = self.options.style.image.embed_images
        if name is None:
            name = "image"
        postfix_html_code = ""  # Additional html code
        if alt is None:
            alt = name
        if alt != "":
            postfix_html_code += f' alt="{alt}"'
        if title is not None and title != "":
            postfix_html_code += f' title="{title}"'
        if isinstance(source, np.ndarray):
            source = Image(source, pixel_format=pixel_format)
        html_lb = "<br>" if br else ""
        if isinstance(source, str):
            if not source.lower().startswith("http") or download:
                source = FileStag.load(source)
            else:
                self._insert_image_reference(
                    name,
                    source,
                    alt,
                    scaling=scaling,
                    max_width=max_width,
                    html_linebreak=br,
                    postfix_html_code=postfix_html_code,
                )
                return
        filename = self.builder.reserve_unique_name(name)
        if isinstance(source, Canvas):
            source = source.to_image()
        file_location = ""
        size_definition = ""
        if scaling != 1.0 or optical_scaling != 1.0 or max_width is not None:
            max_size = None
            if max_width is not None:
                if scaling != 1.0:
                    raise ValueError("Can't set max_size and scaling at the same time.")
                scaling = None
                if isinstance(max_width, float):
                    max_width = int(round(self.builder.max_fig_size.width * max_width))
                    if max_width >= MAXIMUM_IMAGE_WIDTH:
                        raise ValueError(MAX_SIZE_ERROR)
                max_size = (max_width, None)
            if not isinstance(source, Image):
                source = Image(source)
            source = source.resized_ext(factor=scaling, max_size=max_size)
            size_definition = (
                f" width={int(round(source.width * optical_scaling))} "
                f"height={int(round(source.height * optical_scaling))}"
            )
        # encode image if required
        if isinstance(source, bytes):
            encoded_image = source
        else:
            img_format, quality = self.options.style.image.default_filetype
            if filetype is not None:
                if isinstance(filetype, tuple):
                    img_format, quality = filetype
                else:
                    img_format = filetype
            encoded_image = source.encode(filetype=img_format, quality=quality)
        # store on disk if required
        if self.builder.options.output.log_to_disk:
            file_location = self._log_image_to_disk(
                filename, name, source, encoded_image
            )
        # embed if required
        if self.options.style.image.embed_images:
            embed_data = self._build_get_embedded_image(encoded_image)
            file_location = embed_data
        if len(file_location):
            self.builder.add_html(
                f'<img src="{file_location}"{size_definition}{postfix_html_code}>'
                f"{html_lb}\n"
            )
        if (
            self.page_session.txt_export
            or self.page_session.options.output.log_to_stdout
        ):
            if not isinstance(source, Image):
                source = Image(source)
            max_width = min(max(source.width / 800 * 80, 1), 120)
            align, cw = self.builder.get_ascii_alignment()
            if CONSOLE in self.builder.options.output.formats_out:
                method = AsciiImageMethod.GRAY_LEVELS_69
                if not SystemInfo.os_type.is_windows:
                    method = AsciiImageMethod.COLOR_ASCII
                ascii_code = source.to_ascii(
                    max_columns=max_width, min_columns=cw, align=align, method=method
                )
                self.builder.add_txt(ascii_code, align=False, targets={"console"})
            if TXT in self.builder.options.output.formats_out:
                ascii_code = source.to_ascii(
                    max_columns=max_width,
                    min_columns=cw,
                    method=AsciiImageMethod.GRAY_LEVELS_69,
                    align=align,
                )
                self.builder.add_txt(ascii_code, align=False, targets={"txt"})
        else:
            self.builder.add_txt(f"\n[{alt}]")

    def _insert_image_reference(
        self,
        name,
        source,
        alt_text,
        scaling: float = 1.0,
        max_width: int | None = None,
        html_scaling: float = 1.0,
        html_linebreak: bool = True,
        postfix_html_code: str = "",
    ):
        """
        Inserts a link to an image in the html logger without actually
        downloading or storing the image locally

        :param name: The image's name
        :param source: The url
        :param alt_text: The alternative display text
        :param scaling: The scaling factor
        :param max_width: The image's maximum width in pixels
        :param html_scaling: Defines the factor with which the image shall
            be visualized on the html page without really rescaling the image
            itself and thus giving the possibility to zoom in the browser.
        :param html_linebreak: Defines if a linebreak shall be inserted
            after the image
        :param postfix_html_code: Additional text to insert inside the HTML image tag
        """
        html_lb = "<br>" if html_linebreak else ""
        if scaling != 1.0 or html_scaling != 1.0 or max_width is not None:
            image = Image(source)
            if max_width is not None:
                if isinstance(max_width, float):
                    max_width = int(round(self.builder.max_fig_size.width * max_width))
                    if max_width >= MAXIMUM_IMAGE_WIDTH:
                        raise ValueError(MAX_SIZE_ERROR)
                scaling = max_width / image.width
            width, height = (
                int(round(image.width * scaling * html_scaling)),
                int(round(image.height * scaling * html_scaling)),
            )
            self.builder.add_html(
                f'<img src="{source}" width={width} '
                f"height={height}{postfix_html_code}>{html_lb}"
            )
        else:
            self.builder.add_html(f'<img src="{source}"{postfix_html_code}>{html_lb}')
        self.builder.add_md(f"![{name}]({source})\n")
        self.builder.add_txt(f"\n[{alt_text}]\n")

    def _log_image_to_disk(
        self, filename: str, name: str, source: bytes | Image, encoded_image
    ) -> str:
        """
        Stores an image on the disk

        :param filename:  The output filename
        :param name:  The image's name
        :param source: The data source
        :param encoded_image: The encoded image
        :return: The file location of the store image
        """
        file_location = ""
        if isinstance(source, bytes):
            import filetype

            file_type = filetype.guess(source)
            target_filename = (
                self.builder.options.output.target_dir
                + f"/{filename}.{file_type.extension}"
            )
            if self._need_to_store_images_on_disk():
                FileStag.save(target_filename, source)
        else:
            image_format, quality = self.builder.options.style.image.default_filetype
            extension = self.builder.options.style.image.default_filetype[0]
            target_dir = self.builder.options.output.target_dir
            target_filename = target_dir + f"/{filename}.{extension}"
            if self._need_to_store_images_on_disk():
                FileStag.save(target_filename, encoded_image)
        if not self.options.style.image.embed_images:
            file_location = FilePath.basename(target_filename)
        if self.page_session.md_export:
            self.builder.add_md(f"![{name}]({FilePath.basename(target_filename)})\n")
        return file_location

    @staticmethod
    def _build_get_embedded_image(source: bytes) -> str:
        """
        Encodes an image to ASCII to embed it directly into an HTML page

        :param source: The source data
        :return: The string to embed
        """
        ft = filetype.guess(source)
        mime_type = ft.mime
        base64_data = base64.encodebytes(source).decode("ASCII")
        return f"data:{mime_type};base64,{base64_data}"

    def _need_to_store_images_on_disk(self) -> bool:
        """
        Returns if images NEED to be stored on disk

        :return: True if they do
        """
        return self.page_session.md_export or not self.options.style.image.embed_images
