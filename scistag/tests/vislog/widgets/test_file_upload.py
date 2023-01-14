"""
Tests the LFileUpload widget
"""
from .. import vl
from scistag.vislog import VisualLog
from scistag.vislog.widgets import LFileUpload


def test_basic_setup():
    """
    Basic setup and insertion ests
    """
    ll = VisualLog(fixed_session_id="upload").default_builder
    ll.test.checkpoint("upload")
    with ll.align.block_center:
        upload = LFileUpload(
            ll,
            types="videos/*",
            max_file_count=5,
            max_upload_size=10000000,
            gallery_items=0,
            max_gallery_preview_size=500,
            upload_text="Drop videos here",
            button_text="Select videos",
        )
    ll.test.assert_cp_diff("657c209b758d65f8171e13ad61a15af2", target=vl)


def teardown_module(_):
    """
    Finalize the test
    """
    vl.flush()
