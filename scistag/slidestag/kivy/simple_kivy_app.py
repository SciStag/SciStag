import kivy
from kivy.app import App
from kivy.config import Config

from scistag.remotestag import RemoteServiceHandler
from scistag.slidestag import SlideApp, SlideSession
from scistag.slidestag4kivy.embedded_slider import EmbeddedSlider

kivy.require('2.1.0')


class KivyApp(App):
    """
    Minimalistic Kivy application
    """

    def __init__(self, slide_app: SlideApp, session: SlideSession):
        """
        Initializer
        :param slide_app: The application
        :param session: The session
        """
        super(KivyApp, self).__init__()
        self.slide_app: SlideApp = slide_app
        self.slide_session: SlideSession = session
        self.main_view = None

    def build(self):
        self.main_view = EmbeddedSlider(size=self.slide_session.resolution,
                                        size_hint=(None, None))
        self.main_view.set_session(self.slide_session)
        self.title = self.slide_session.title
        return self.main_view


def run_simple_kivy_app(slide_app: "SlideApp"):
    """
    Hosts the SlideApp via Kivy
    :param slide_app: The application
    """
    session: SlideSession = slide_app.setup_session()
    RemoteServiceHandler.get_default_handler().start()
    Config.set('graphics', 'width', str(session.resolution[0]))
    Config.set('graphics', 'height', str(session.resolution[1]))
    KivyApp(slide_app, session).run()
