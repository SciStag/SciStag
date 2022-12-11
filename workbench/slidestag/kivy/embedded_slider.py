from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from kivy.clock import Clock
from .advanced_image import AdvancedImage

if TYPE_CHECKING:
    from scistag.slidestag.slide_session import SlideSession


class EmbeddedSlider(AdvancedImage):
    """
    Allows the embedding of a slide application into a Kivy application
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_frequency = 1 / 30.0
        self.allow_stretch = False
        self.auto_size = True
        self.timer = Clock.schedule_interval(self.handle_timer, self.update_frequency)
        self.session: SlideSession | None = None
        self.bind(on_touch_down=self.handle_touch_down)
        self.bind(on_touch_up=self.handle_touch_up)
        self.bind(on_touch_move=self.handle_touch_move)

    def set_session(self, session: SlideSession):
        """
        Defines the session to be handled by the widget
        :param session: The SlideSession
        """
        self.session = session

    def handle_touch_move(self, widget, event):
        tm_event = {"type": "tapMove", "coord": (int(event.pos[0]), int(event.pos[1]))}
        self.session.handle_user_data(self.session.USER_DATA_CLIENT_EVENTS, [tm_event])
        return True

    def handle_touch_down(self, widget, event):
        td_event = {"type": "tapDown", "coord": (int(event.pos[0]), int(event.pos[1]))}
        self.session.handle_user_data(self.session.USER_DATA_CLIENT_EVENTS, [td_event])
        return True

    def handle_touch_up(self, widget, event):
        tu_event = {"type": "tapUp", "coord": (int(event.pos[0]), int(event.pos[1]))}
        self.session.handle_user_data(self.session.USER_DATA_CLIENT_EVENTS, [tu_event])
        return True

    def handle_timer(self, timer):
        if self.session is None:
            return True
        config = {}
        newest_frame = self.session.render_to_pil(config=config)
        self.set_image_data(np.array(newest_frame))
        return True
