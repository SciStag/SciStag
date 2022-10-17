import pytest

from scistag.common import ConfigStag
from scistag.tests.slidestag.test_common import slide_session
from scistag.slidestag.slide_session import SlideSession
from . import skip_slidestag


@pytest.mark.skipif(skip_slidestag, reason="SlideStag tests disabled")
def test_session(slide_session: SlideSession):
    assert len(slide_session.session_id) == 22
    assert len(slide_session.get_media_paths()) > 0
    assert len(slide_session.update_config().get(SlideSession.SESSION_ID)) == 22
