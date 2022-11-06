import pytest

from scistag.common import ConfigStag
from scistag.tests.slidestag.test_common import log_image_data, slide_session
from scistag.slidestag.slide_session import SlideSession
from . import skip_slidestag


@pytest.mark.skipif(skip_slidestag, reason="SlideStag tests disabled")
def test_window(slide_session: SlideSession):
    config = {}
    view_data = slide_session.render_and_compress(config=config)
    log_image_data("test_window.jpg", view_data)
