"""
A simple Hello world! application displaying "Hello world!" and displaying a
Stag emoji
"""

from scistag.imagestag import Canvas, Image
from scistag.imagestag.emoji import EmojiDb
from scistag.slidestag import Slide, SimpleSlide


def paint(slide: Slide, canvas: Canvas):
    font = canvas.get_font("JetBrains Mono", size=72)
    text = "Hello SciStag!"
    x = slide.width() // 2 - font.get_covered_area(text).lr.x // 2
    canvas.text(
        (x, 70),
        text=text,
        color=(255, 0, 0),
        font=font,
        stroke_color=(0, 0, 0),
        stroke_width=2,
    )
    emoji: Image = slide.cache_data(
        "emoji", lambda: EmojiDb.render_emoji(":deer:", size=512)
    )
    canvas.draw_image(emoji, (slide.width() // 2 - emoji.width // 2, 220))


if __name__ == "__main__":
    app = SimpleSlide.create_simple_app(
        title="Hello SciStag!", on_paint=paint, resolution=(700, 768)
    )
    app.run_as_kivy_app()
