from __future__ import annotations
from typing import TYPE_CHECKING, Union

from pydantic import BaseModel

from threading import RLock
import time
import re
from scistag.datastag.data_stag_connection import DataStagConnection

if TYPE_CHECKING:
    from scistag.slidestag.slide_application import SlideApp


class SessionConfig(BaseModel):
    """
    The base class of a session configuration
    """

    session_id: str
    "Defines the session's ID"
    app: Union["SlideApp", None] = None
    "Defines the application class to be used"


class Session:
    """
    Represents a single user data session
    """

    def __init__(self, config: SessionConfig) -> None:
        """
        Initializer

        :param config: The session configuration dictionary.
        """
        self.lock = RLock()
        "Multithread access lock"
        self.unloaded = False
        """
        Set to true when the app is going to be destroyed and should not be used
        anymore
        """
        self.app: SlideApp | None = config.app
        self.session_id = config.session_id
        "The unique session identifier"
        self.guest_id = None
        "Access id for guest access"
        self.guest_data: bytes | None = None
        "Contains the previous image cached for a guest viewer"
        self._config = config
        "The configuration dictionary"
        self.last_interaction = 0.0
        "Last interaction to manage garbage collection in seconds"
        self.session_timeout = 0.0
        "The session timeout in seconds. 0.0 = no timeout"
        self.handle_used()
        self.user_data_config = {}
        "registered user data elements"
        self.session_data_root_path = f"remotestag.sessions.{self.session_id}."
        self.user_data_root_path = f"{self.session_data_root_path}userData."
        self.data_connection = DataStagConnection()
        "Local database connection"
        self.default_user_data_timeout = 5.0

    def update_config(self) -> SessionConfig:
        """
        Returns the current configuration

        :return: The configuration
        """
        return self._config

    def handle_used(self) -> None:
        """
        Should be called when the  session was requested
        """
        self.last_interaction = time.time()

    def handle_user_data(self, user_data_name: str, data: bytes):
        """
        Requests if the user data  shall be handled manually.

        Otherwise it 's stored in {rootPath}.userData

        :param user_data_name: The data 's identifier
        :param data: The data to be set
        :return: True if the data shall not be stored in the vault
        """
        return False

    def set_user_data(self, user_data_name: str, data: bytes) -> None:
        """
        Stores user data provided from the browser

        :param user_data_name: The user data's name (alpha numeric)
        :param data: The data
        """
        assert re.match(r'^[A-Za-z0-9_]+$', user_data_name)
        if self.handle_user_data(user_data_name, data):
            return
        self.data_connection.set_ts(
            f"{self.user_data_root_path}{user_data_name}", data=data,
            timeout_s=self.default_user_data_timeout,
            timestamp=time.time())

    def handle_load(self):
        """
        Is called right after the constructor and before the build call

        :return:
        """
        pass

    def handle_unload(self):
        """
        Called when the session shall deallocate memory intensive resources
        """
        self.data_connection.delete_multiple(
            [
                self.session_data_root_path + "*"])
        # delete all old data related to our session

    def set_guest_data(self, data: bytes):
        """
        Backups the last data for a guest viewer

        :param data: The last image
        """
        self.guest_data = data

    def get_guest_data(self) -> bytes | None:
        """
        Returns the last guest data

        :return: The last guest data
        """
        return self.guest_data
