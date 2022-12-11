from __future__ import annotations
from threading import RLock
from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.slidestag.slide_session import SlideSession

from scistag.remotestag import RemoteServiceHandler
from scistag.remotestag.session import Session
import os


class SlideApp:
    """
    Defines a registered application hosted by the slide server
    """

    def __init__(self, app_name: str, session_class: Type[Session]) -> None:
        """
        Initializer

        :param app_name: The app's unique name
        :param session_class: The class of the application session
        """
        self.app_name = app_name
        self.session_class: Type[Session] = session_class
        self.media_paths = ["", os.path.dirname(__file__) + "/media"]
        self.lock = RLock()

    def prepare_session_int(self, config: dict) -> SlideSession:
        """
        Requests the configuration of a new session

        :param config: The configuration dictionary. has to contain at least the sessionId
        """
        config["app"] = self
        new_session: SlideSession = self.session_class(config)
        new_session.handle_load()
        new_session.build()
        new_session.run()
        return new_session

    def get_media_paths(self) -> []:
        """
        Returns a list of all media paths
        :return: A list of all registered media directories
        """
        with self.lock:
            return list(self.media_paths)

    def register(self) -> SlideApp:
        """
        Registers the application and returns it
        :return: The app handle
        """
        from scistag.slidestag.slide_application_manager import SlideAppManager

        SlideAppManager.get().register_application(self)
        return self

    def setup_session(self) -> SlideSession | None:
        """
        Setups a session via the SlideAppManager and returns it
        """
        from scistag.slidestag.slide_application_manager import SlideAppManager

        session = SlideAppManager.shared_app_manager.create_session(self.app_name)
        return session

    def run_as_kivy_app(self):
        """
        Runs the application within Kivy
        """
        from scistag.slidestag4kivy.simple_kivy_app import run_simple_kivy_app

        run_simple_kivy_app(self)

    def run_as_web_app(
        self,
        host_name: str = "0.0.0.0",
        port: int = 5020,
        ssl_context: tuple[str, str] | None = None,
        verbose=False,
    ):
        """
        Runs the application via Flask. Note that this is only a very
        minimalistic implementation for fast prototyping.

        For more advanced hosting set up a single process Gunicorn server.
        To this you just have to add the the slidestag_service blueprint to
        your Flask server (scistag.slidestag4flask) and you are ready to go.

        :param app: The application handle.
        :param host_name: The host name (e.g. IP) such as 0.0.0.0 or 127.0.0.1
        :param port: The port at which the service shall be hosted.
        :param ssl_context: The SSL certificate and key. If provided the service
            will be hosted via https
        :param verbose: Stfu.
        :return: The function never returns.
        """
        RemoteServiceHandler.get_default_handler().start()
        protocol = "http" if ssl_context is None else "https"
        if not verbose:
            print(
                f"\n* View your app at --> {protocol}://{host_name}:{port}/apps/{self.app_name} <--\n",
                flush=True,
            )
        from scistag.slidestag4flask import SimpleSlideServer

        SimpleSlideServer.run_simple_server(
            host_name=host_name, port=port, ssl_context=ssl_context
        )
