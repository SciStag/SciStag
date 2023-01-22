"""
Implements tests for the class LogServiceExtension
"""
import pytest

from scistag.filestag import FilePath
from scistag.vislog import VisualLog
from scistag.webstag.server import WebRequest, WebResponse


def test_service_extension_publish():
    """
    Tests the basics of publishing and providing services
    """
    # disk
    options = VisualLog.setup_options("disk")
    options.output.target_dir = FilePath.absolute_comb("logs/serviceLog")
    my_log = VisualLog(options=options)
    builder = my_log.default_builder
    abs_path = FilePath.absolute_comb("./embedded.md")
    builder.service.publish("embedded.md", abs_path, embeddable=False)
    builder.service.publish("embedded2.md", abs_path, embeddable=True)
    img = builder.emoji("*globe*", return_image=True).encode("png")
    builder.service.publish("emoji.png", img, embeddable=False)
    with pytest.raises(FileNotFoundError):
        builder.service.publish("notExising.md", "notExisting", embeddable=False)
    assert builder.service.get_file("embedded.md") is not None
    result = builder.service.get_file("emoji.png")
    assert result is not None
    assert result.mimetype == "image/png"
    assert builder.service.get_file("notExisting") is None
    # in-memory
    options = VisualLog.setup_options()
    options.output.target_dir = FilePath.absolute_comb("logs/serviceLog")
    my_log = VisualLog(options=options)
    builder = my_log.default_builder
    builder.service.publish("embedded.md", abs_path, embeddable=False)
    options = VisualLog.setup_options("disk")
    options.output.single_file = True
    my_log = VisualLog(options=options)
    builder = my_log.default_builder
    abs_path = FilePath.absolute_comb("./embedded.md")
    builder.service.publish("embedded.md", abs_path, embeddable=True)


def test_web_requests():
    """
    Tests the web request features
    """
    options = VisualLog.setup_options()
    my_log = VisualLog(options=options)
    builder = my_log.default_builder

    def service_handler(request) -> WebResponse:
        response = WebResponse(b"123")
        response.mimetype = "test/done"
        return response

    wr = WebRequest(path="live")
    builder.service.publish("testService", service_handler)
    result = builder.service.handle_web_request(wr)
    assert result.mimetype == "text/html"
    wr = WebRequest(path="testService")
    result = builder.service.handle_web_request(wr)
    assert result.mimetype == "test/done"
    abs_path = FilePath.absolute_comb("./embedded.md")
    builder.service.publish("embedded.md", abs_path, embeddable=False)
    wr = WebRequest(path="embedded.md")
    result = builder.service.handle_web_request(wr)
    assert len(result.body) == 51
