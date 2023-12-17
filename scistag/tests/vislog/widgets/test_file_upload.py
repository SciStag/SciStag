"""
Tests the LFileUpload widget
"""
from scistag.webstag.server import FileAttachment, WebRequest
from .. import vl
from scistag.vislog import VisualLog
from scistag.vislog.widgets import LFileUpload, LFileUploadEvent


def test_basic_setup():
    """
    Basic setup and insertion ests
    """
    options = VisualLog.setup_options()
    options.output.setup(formats={"html", "txt", "md"})
    ll = VisualLog(options=options, fixed_session_id="upload").default_builder
    ll.test.checkpoint("upload")
    with ll.align.block_center:
        upload = LFileUpload(
            ll,
            types="video/*",
            max_file_count=5,
            max_upload_size=10000000,
            gallery_items=0,
            max_gallery_preview_size=500,
        )
    assert b"drop the videos" in ll.page_session.render_element()[1]
    ll.test.assert_cp_diff("fb65da8adbdc432b225b62b573dcb9a3", target=vl)
    with ll.align.block_center:
        upload = LFileUpload(
            ll,
            types="image/*",
            max_file_count=5,
            max_upload_size=10000000,
            gallery_items=0,
            max_gallery_preview_size=500,
        )
    assert b"drop the images" in ll.page_session.render_element()[1]
    upload = LFileUpload(
        ll,
        types="file/*",
        gallery_items=0,
        upload_text="drop the files here",
        button_text="Select files",
        insert=False,
    )
    assert b"drop the files" not in ll.page_session.render_element()[1]
    upload.insert_into_page()
    assert b"drop the files" in ll.page_session.render_element()[1]


def test_upload():
    file_uploaded: bool = False

    def fupl_callback(event: LFileUploadEvent):
        nonlocal file_uploaded
        assert event.upload_session_id == "123"
        assert len(event.files) == 2
        assert event.files[0].filename == "testfile.bin"
        assert event.files[0].data == b"test123"
        file_uploaded = True

    ll = VisualLog(fixed_session_id="upload").default_builder
    button = ll.widget.button()
    upload = LFileUpload(
        ll,
        types="file/*",
        gallery_items=0,
        upload_text="drop the files here",
        button_text="Select files",
        on_upload=fupl_callback,
    )
    upload_event = LFileUploadEvent(upload_session_id="123", widget=None)
    upload.handle_event(upload_event)
    assert not file_uploaded

    dummy_file = FileAttachment("testfile.bin", b"test123")
    web_request = WebRequest()
    web_request.files.append(dummy_file)
    web_request.form = {
        "uploadId": "123",
        "fileIndex": 0,
        "fileCount": 2,
        "widget": upload.identifier,
    }
    ll.service.handle_file_upload(web_request)
    web_request.form = {
        "uploadId": "123",
        "fileIndex": 0,
        "fileCount": 2,
        "widget": "unknown",
    }
    response = ll.service.handle_file_upload(web_request)
    assert response.status == 400 and b"unknown target" in response.body
    web_request.form = {
        "uploadId": "123",
        "fileIndex": 0,
        "fileCount": 2,
        "widget": button.identifier,
    }
    response = ll.service.handle_file_upload(web_request)
    assert response.status == 400 and b"invalid widget" in response.body
    web_request.form = {
        "uploadId": "123",
        "fileIndex": 0,
        "fileCount": 2,
        "widget": "",
    }
    response = ll.service.handle_file_upload(web_request)
    assert response.status == 400 and b"no widget name" in response.body
    web_request.form = {"uploadId": "123", "fileIndex": 1, "fileCount": 2}
    upload.handle_file_upload(web_request)
    # test w/ empty session
    web_request.form = {"uploadId": "", "fileIndex": 1, "fileCount": 2}
    upload.handle_file_upload(web_request)
    # test w/ file out of range
    web_request.form = {"uploadId": "123", "fileIndex": 2, "fileCount": 2}
    upload.handle_file_upload(web_request)
    # file index twice
    web_request.form = {"uploadId": "123", "fileIndex": 1, "fileCount": 2}
    upload.handle_file_upload(web_request)
    web_request.form = {"uploadId": "123", "fileIndex": 1, "fileCount": 2}
    upload.handle_file_upload(web_request)

    assert "outfile" not in ll.cache
    upload.target = "outfile"
    # w cache target
    web_request.files.append(dummy_file)
    web_request.form = {"uploadId": "123", "fileIndex": 0, "fileCount": 2}
    upload.handle_file_upload(web_request)
    web_request.form = {"uploadId": "123", "fileIndex": 1, "fileCount": 2}
    upload.handle_file_upload(web_request)
    assert "outfile" in ll.cache
    assert ll.cache.lpop("outfile")[0].data == b"test123"

    upload.handle_event(upload_event)
    assert file_uploaded
    file_uploaded = False

    upload_event = LFileUploadEvent(upload_session_id="123", widget=upload)
    upload_event.files += [dummy_file, dummy_file]
    upload.handle_event(upload_event)
    assert file_uploaded
    upload.on_upload = None
    file_uploaded = False
    upload.handle_event(upload_event)
    assert not file_uploaded


def teardown_module(_):
    """
    Finalize the test
    """
    vl.flush()
