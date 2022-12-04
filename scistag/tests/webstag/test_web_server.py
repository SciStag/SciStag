"""
Tests the WebStagServer
"""
import time

import pytest

import scistag.common
from scistag.webstag import web_fetch
from scistag.webstag.server import WebStagServer, WebClassService


class SimpleClass:

    def get_hello_world(self):
        return "Hello world"


def test_init():
    """
    Tests the basic server initialization
    :return:
    """
    server = WebStagServer(host_name="127.0.0.1", port=0, silent=False)
    server._setup_logging()
    assert server.port != 0

    if scistag.common.SystemInfo.os_type == \
            scistag.common.SystemInfo.os_type.LINUX:
        with pytest.raises(OSError):
            WebStagServer(host_name="127.0.0.1", port=(389, 389),
                          silent=True)
    server = WebStagServer(host_name="127.0.0.1", port=(4000, 4100),
                           silent=True)
    assert 4000 <= server.port <= 4100

    class_service = WebClassService(service_name="simple")
    class_service.add_class(SimpleClass, service_name=None)
    class_service.add_class(SimpleClass, service_name="serviceName")
    server.add_service(class_service)
    assert len(server.services) == 1

    # for coverage only
    WebStagServer._disabled_server_banner()
    server._setup_logging()
    assert server.handle is None
    assert not server.started

    assert not server.kill()

    server.start(mt=True)
    for rep in range(20):
        time.sleep(0.05)
        if server.started:
            break
    assert server.handle is not None
    assert server.started
    fetch = web_fetch(f"http://127.0.0.1:{server.port}/serviceName/helloWorld")
    assert fetch == b"Hello world"
    server.kill()
