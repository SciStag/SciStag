from __future__ import annotations
import time
from threading import RLock
import uuid
import base64
from .session import Session


class SessionHandler:
    """
    Handles all of this server's sessions
    """

    shared_handler: SessionHandler = None

    def __init__(self):
        self.session_lock = RLock()  # The session access lock
        self.sessions = {}  # The session dictionary

    def get_session(self, session_id: str) -> Session | None:
        """
        Returns a session by id.

        :param session_id: The session's id. See create_session_id
        """
        with self.session_lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                if session.unloaded:
                    return None
                return session
            return None

    def get_session_by_guest_id(self, guest_id: str) -> Session | None:
        """
        Returns a session by guest id.

        :param guest_id: The session guest's identifier.
        """
        with self.session_lock:
            for session in self.sessions.values():
                if session.guest_id is None or session.guest_id != guest_id:
                    continue
                if session.unloaded:
                    continue
                if session.guest_id is not None and session.guest_id == guest_id:
                    return session
        return None

    def register_session(self, session: "Session"):
        """
        Registers a new session

        :param session: The session object
        """
        with self.session_lock:
            assert session.session_id not in self.sessions
            self.sessions[session.session_id] = session

    def garbage_collect(self):
        """
        Removes deprecated sessions
        :return:
        """
        cur_time = time.time()
        with self.session_lock:
            sessions = list(self.sessions.values())
        garbage = []
        for session in sessions:
            with session.lock:
                if session.session_timeout is None or session.session_timeout == 0:
                    continue
                if (
                    cur_time - session.last_interaction > session.session_timeout
                ):  # session timeout
                    garbage.append(session)
                    session.unloaded = True
                    session.handle_unload()
        with self.session_lock:
            for session in garbage:
                if session.session_id in self.sessions:
                    del self.sessions[session.session_id]

    @staticmethod
    def create_session_id() -> str:
        """
        Creates a unique session identifier and ASCII encodes it so it can be used in URLs

        :return: ASCII encoded UUID
        """
        return base64.urlsafe_b64encode(uuid.uuid1().bytes).rstrip(b"=").decode("ascii")

    @staticmethod
    def session_id_to_uuid(session_id: str) -> uuid.UUID:
        """
        Decodes an ASCII encoded UUID and returns it

        :param session_id: The session id
        :return: The original UUID
        """
        return uuid.UUID(bytes=base64.urlsafe_b64decode(session_id + "=="))


SessionHandler.shared_handler = SessionHandler()
