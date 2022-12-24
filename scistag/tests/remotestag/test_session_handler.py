"""
Tests the class SessionHandler which handles remote execution user sessions
"""
import time
from uuid import UUID

from scistag.common.time import sleep_min
from scistag.remotestag import SessionHandler, Session, SessionConfig


def test_session_handler():
    """
    Tests the SessionHandler class base functionality
    """

    session_id = SessionHandler.create_session_id()
    guest_id = SessionHandler.create_session_id()
    config = SessionConfig(session_id=session_id)
    session = Session(config=config)
    session.guest_id = guest_id

    assert len(session_id) == 22

    uid = SessionHandler.session_id_to_uuid(session_id)
    assert isinstance(uid, UUID)

    assert SessionHandler.shared_handler.get_session("123") is None

    # provoke garbage collection
    SessionHandler.shared_handler.register_session(session)

    assert SessionHandler.shared_handler.get_session(session_id) == session
    assert SessionHandler.shared_handler.get_session_by_guest_id(guest_id) == session
    assert SessionHandler.shared_handler.get_session_by_guest_id("123") is None

    session.session_timeout = None
    SessionHandler.shared_handler.garbage_collect()
    session.session_timeout = 2.0
    SessionHandler.shared_handler.garbage_collect()
    sleep_min(0.05)
    session.session_timeout = 0.05
    SessionHandler.shared_handler.garbage_collect()

    assert SessionHandler.shared_handler.get_session(session_id) is None
