from __future__ import annotations
from threading import RLock
from scistag.common import get_edp
from scistag.filestag import FileStag
from scistag.imagestag.font import Font


class RegisteredFont:
    """
    A registered font contains information about a single available font and
    it's style variations.

    Upon request it can be used to create a real font handle with the specified
    properties such as weight and style.
    """

    def __init__(self, font_face: str, base_path: str,
                 variations: list[tuple[str, set[str]]]):
        """
        :param font_face: The font's face name, e.g. Roboto
        :param base_path: Base file name without extension,
            e.g. /home/user/myProject/fonts/Roboto
        :param variations: The single font variations. The flags (e.g. "Bold")
            as string and the file name extension,
        e.g. "-Bold")
        """
        self.font_face = font_face
        "The font face's name"
        self.base_path = base_path
        "The filename base path (excluding variations)"
        self.extension = ".ttf"
        "The file extension"
        self.variable_weight = 'wght' in variations[0][0]
        "Has the font a totally flexible weight?"
        self.variations = variations
        "Different main variations, e.g. Italic"

    def get_handle(self, size: int, flags: set[str] | None = None) -> \
            Font | None:
        """
        Tries to create a font handle for given font
        :param size: The font's size
        :param flags: The flags such as {'Bold'} or {'Bold', 'Italic'}
        :return: On success the handle of the font
        """
        if flags is None:
            flags = set()
        from scistag.imagestag.font import Font, ImsFramework
        for variation in self.variations:
            if flags == variation[1]:
                full_name = self.base_path + variation[0] + self.extension
                data = FileStag.load(full_name)
                font = Font(source=data, size=size, framework=ImsFramework.PIL)
                return font
        return None


class FontRegistry:
    """
    Manages all available fonts which can be used from (especially) ImageStag
    and SlideStag.
    """
    access_lock = RLock()
    "Multi-thread access lock"
    _base_fonts_registered = False
    "Defines if the base fonts were configured already"
    fonts = {}
    "Dictionary of registered fonts"

    @classmethod
    def register_font(cls, font_face: str, base_path: str,
                      variations: list[tuple[str, set[str]]]):
        """
        Registers a single font. See _register_base_fonts for examples.

        :param font_face: The font's face name, e.g. Roboto
        :param base_path: Base file name without extension,
            e.g. /home/user/myProject/fonts/Roboto
        :param variations: The single font variations. The flags (e.g. "Bold")
            as string and the file name extension,
        e.g. "-Bold")
        """
        if not cls._base_fonts_registered:
            cls._ensure_setup()
        with cls.access_lock:
            if font_face in cls.fonts:
                raise ValueError("Font was already registered")
            cls.fonts[font_face] = RegisteredFont(font_face=font_face,
                                                  base_path=base_path,
                                                  variations=variations)

    @classmethod
    def get_font(cls, font_face: str, size: int,
                 flags: set[str] | None = None) -> Font | None:
        """
        Tries to create a font handle for given font

        :param font_face: The font's face
        :param size: The font's size
        :param flags: The flags such as {'Bold'} or {'Bold', 'Italic'}
        :return: On success the handle of the font
        """
        if not cls._base_fonts_registered:
            cls._ensure_setup()
        reg_font = None
        with cls.access_lock:
            if font_face in cls.fonts:
                reg_font = cls.fonts[font_face]
            if reg_font is None:
                return None
        return reg_font.get_handle(size, flags)

    @classmethod
    def get_fonts(cls):
        """
        Returns a list of all fonts

        :return: A list of all registered fonts and their variations
        """
        with cls.access_lock:
            import copy
            return copy.deepcopy(cls.fonts)

    @classmethod
    def _ensure_setup(cls):
        """
        Ensures the standard fonts were set up
        """
        with cls.access_lock:
            if not cls._base_fonts_registered:
                cls._base_fonts_registered = True
                cls._register_base_fonts()

    @classmethod
    def _register_base_fonts(cls):
        """
        Registers the standard fonts which shipped with SciStag
        """
        edp = get_edp()
        FontRegistry.register_font(font_face="Roboto",
                                   base_path=edp + "fonts/Roboto/Roboto",
                                   variations=[('-Regular', set()),
                                               ('-Italic', {'Italic'}),
                                               ('-Black', {'Black'}),
                                               ('-Bold', {'Bold'}),
                                               ('-Medium', {'Medium'}),
                                               ('-Light', {'Light'}),
                                               ('-Thin', {'Thin'}),
                                               ('-BlackItalic',
                                                {'Black', 'Italic'}),
                                               ('-BoldItalic',
                                                {'Bold', 'Italic'}),
                                               ('-MediumItalic',
                                                {'Medium', 'Italic'}),
                                               ('-LightItalic',
                                                {'Light', 'Italic'}),
                                               ('-ThinItalic',
                                                {'Thin', 'Italic'})])
        FontRegistry.register_font(font_face="Roboto Flex",
                                   base_path=edp + \
                                             "fonts/RobotoFlex/RobotoFlex[GRAD,XOPQ,XTRA,YOPQ,YTAS,YTDE,YTFI,YTLC,YTUC,opsz,slnt,wdth,wght].ttf",
                                   variations=[('', set()),
                                               ('-Italic', {'Italic'})])
        FontRegistry.register_font(font_face="JetBrains Mono",
                                   base_path=edp + "fonts/JetBrains Mono/JetBrainsMono",
                                   variations=[('[wght]', set()),
                                               ('-Italic[wght]', {'Italic'})])
