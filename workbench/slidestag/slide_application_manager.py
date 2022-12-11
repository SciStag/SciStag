from __future__ import annotations
from threading import RLock
from .slide_application import SlideApp
from .slide_session import SlideSession
from scistag.remotestag import SessionHandler, Session


class SlideAppManager:
    """
    Managed the applications
    """

    shared_app_manager: SlideAppManager = None

    def __init__(self):
        """
        Initializer
        """
        self.lock = RLock()
        self.registered_applications: dict[str, SlideApp] = {}

    def register_application(self, application: SlideApp) -> None:
        """
        Registers a new application.

        :param application: The application handler
        """
        with self.lock:
            if application.app_name in self.registered_applications:
                if self.registered_applications[application.app_name] == application:
                    return
                raise Exception("Application name already registered")
            self.registered_applications[application.app_name] = application

    def app_is_valid(self, app_name) -> bool:
        """
        Returns if given application name is valid

        :param app_name: The app's name
        :return: True on success
        """
        with self.lock:
            return app_name in self.registered_applications

    def create_session(
        self, app_name: str, config: dict | None = None, register=True
    ) -> Session | None:
        """
        Creates a new instance of a given application type and registers it in
        the session handler

        :param app_name: The application's name
        :param config: The application's configuration
        :param register: Defines if the session shall be registered
        :return: The session. None if the creation failed
        """
        if config is None:
            config = {}
        with self.lock:
            if app_name not in self.registered_applications:
                return None
            app = self.registered_applications[app_name]
        session_id = config.get(Session.SESSION_ID, None)
        if session_id is None:
            session_id = SessionHandler.create_session_id()
            config[Session.SESSION_ID] = session_id
        config[Session.PERMISSIONS] = {
            SlideSession.PERMISSION_INPUT: False,
            SlideSession.PERMISSION_WEBCAM: False,
        }
        session = app.prepare_session_int(config)
        if register:
            SessionHandler.shared_handler.register_session(session)
        return session

    @classmethod
    def get(cls) -> "SlideAppManager":
        """
        Returns the shared app manager
        :return: The app manager
        """
        return cls.shared_app_manager


SlideAppManager.shared_app_manager = SlideAppManager()
