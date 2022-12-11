from __future__ import annotations
import threading
import io
import os

from scistag.imagestag import Image, Color, ColorTypes

CAIRO_MAC_PORTS_PATH = "/opt/local/lib"
"Path where Cairo can be found if installed via Mac Ports"
CAIRO_BREW_PATH = "/opt/homebrew/lib"
"Path where Cairo can be found if installed via Brew"


def _show_cairo_msg():
    """
    Prints a warning message that either the Cairo package or libraries are
    missing.
    """
    print(
        "\nCairoSVG graphics rendering not available, high-quality rendering "
        "disabled.\n\n"
        "Install Cairo on Linux, in Docker containers or in Windows "
        "Subsystem for Linux (WSL)\n"
        'via "pip install scistag[svg]" or "pip install cairosvg" for the '
        "module and the\n"
        'required library via "sudo apt-get install cairosvg"\n\n'
        "On OS X you can install Cairo via `sudo port install cairo ` or `brew install cairo libxml2 libffi`\n\n"
        "Call scistag.imagestag.SvgRenderer.set_verbose(true) to suppress this "
        "message\n"
        "See help(scistag.imagestag.SvgRenderer) for further details"
    )


class SvgRenderer:
    """
    SVG rendering class which renders an SVG using the Cairo SVG library.

    Important:
    This class requires Cairo being installed on your system. For Linux and OS X
    users this is usually a one-liner, see
    https://www.cairographics.org/download/.

    All standard SciStag Docker images already contain the pre-installed Cairo
    SVG and other base tools, so there is nothing for you to do.
    (https://hub.docker.com/r/scistag)

    If you are a Windows user:
    It is in general possible to build Cairo for Windows too but after days of
    recherche and just stumbling over often more than 10+ years outdated last
    updates on the official sites I decided that this is not a "clean" solution.
    In consequence I converted all essential SVGs tof pre-rendered PNGs - such
    as basic UI graphics, emojis, country flags etc. - to the module so that SVG
    rendering is not required in general for using 98% of the
    functions of SciStag.

    To suppress this message call scistag.imagestag.SvgRenderer.set_verbose() at
    the beginning of your script. Alternatively you can set the
    SCISTAG_SUPPORT_SVG environment variable to 0.

    If you do need hi-quality live rendered SVGs in your application we
    recommend using Docker for Windows and using one of our provided Docker
    images available on https://hub.docker.com/r/scistag.

    If you do not want to dockerize your application then running and debugging
    your application via WSL2 is also workaround, see
    https://thecodeblogger.com/2020/09/24/wsl-setup-vs-code-for-python-development/ or
    https://www.jetbrains.com/help/pycharm/using-wsl-as-a-remote-interpreter.html

    To keep track of the status see https://github.com/SciStag/SciStag/issues/2

    Usage:
    ``` py
    from scistag.imagestack import SvgRenderer
    my_svg = open("example.svg").read()
    image = SvgRenderer.render(my_svg)
    ```
    """

    _access_lock = threading.RLock()
    _verbose = os.environ.get("SCISTAG_SUPPORT_SVG", 1) == 0
    _initialized = False
    _svg_to_png = None
    _cairo_available = False

    @classmethod
    def _setup(cls):
        """
        Setups the svg renderer and tries to initialize Cairo
        :return:
        """
        with cls._access_lock:
            if cls._initialized:
                return
            old_dir = os.getcwd()
            search_paths = [".", CAIRO_MAC_PORTS_PATH, CAIRO_BREW_PATH]
            for path in search_paths:
                if os.path.exists(path):
                    os.chdir(path)
                try:
                    import cairosvg

                    cls._cairo_available = True
                    cls._svg_to_png = cairosvg.svg2png
                    break
                except (OSError, ModuleNotFoundError):
                    cls._cairo_available = False
            if not cls._cairo_available and not cls._verbose:
                _show_cairo_msg()
            os.chdir(old_dir)
            cls._initialized = True

    @classmethod
    def available(cls) -> bool:
        """
        Returns if SVG rendering is available

        :return: True if it is
        """
        with cls._access_lock:
            if not cls._initialized:
                cls._setup()
            return cls._cairo_available

    @classmethod
    def render(
        cls,
        svg_data: bytes,
        output_width=None,
        output_height=None,
        bg_color: ColorTypes | None = None,
    ) -> Image | None:
        """
        Renders an SVG

        :param svg_data: The SVG's data
        :param output_width: The desired output with. Optional.
        :param output_height: The desired output height. Optional.
        :param bg_color: If specified the background will be filled with this
            color
        :return: The image if the rendering was successful. None otherwise.
        """
        with cls._access_lock:
            if not cls._cairo_available or cls._svg_to_png is None:
                return None
            image_data = io.BytesIO()
            if bg_color is not None:
                bg_color = Color(bg_color).to_hex()
            cls._svg_to_png(
                svg_data,
                write_to=image_data,
                output_width=output_width,
                output_height=output_height,
                background_color=bg_color,
            )
            return Image(image_data.getvalue())

    @classmethod
    def set_verbose(cls, value=True):
        """
        Defines if warnings about Cairo not being available shall be suppressed

        :param value: The new value. True = suppress warnings
        """
        cls._verbose = value
