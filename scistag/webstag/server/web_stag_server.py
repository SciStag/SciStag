"""
The WebStagServer is a wrapper around a classic Flask and/or FastAPI server
and shall help setting it up even easier.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from threading import Thread

if TYPE_CHECKING:
    from flask import Flask

from scistag.common import StagLock
from scistag.webstag.server.web_stag_service import WebStagService


class WebStagServer:
    """
    Provides an easy setup for hosting Flask web (and soon also FastAPI)
    web services.
    """

    def __init__(self, services: list[WebStagService] | None = None,
                 host_name: str = "127.0.0.1",
                 port: int | tuple[int, int] = 8010,
                 flask_ssl_context=None,
                 silent=False):
        """
        :param services: The initial set of services to use
        :param host_name: The host name under which the service shall be
            hosted.

            Examples:
            - 127.0.0.1 = local connections only
            - 0.0.0.0 = all available network interfaces
        :param port: The TCP port at which the service shall be hosted.

            Either an explicit port or a range tuple to search within.
            If 0 is passed a random port will be selected.
        :param flask_ssl_context: Advanced SSL context settings, see
            https://werkzeug.palletsprojects.com/en/2.2.x/serving/#werkzeug.serving.run_simple
        :param silent: Defines if server logs and other output to stdout
            shall be silenced.
        """
        self._access_lock = StagLock()
        "Thread-safe access lock to shared data"
        self._flask: "Flask" | None = None
        "The Flask handle"
        self._services: list[WebStagService] = \
            services if services is not None else []
        "The services to be hosted"
        self._started = False
        "Defines if the server was started already"
        self.server_thread: Thread | None = None
        "The thread which executes the server"
        self.host_name = host_name
        if port == 0:
            port = (0, 0)
        if isinstance(port, tuple):
            from scistag.netstag import NetHelper
            free_ports = NetHelper.find_free_ports(host_name,
                                                   port_range=port,
                                                   count=1)
            if len(free_ports) == 0:
                raise OSError("No free network port found")
            port = free_ports[0]
        """
        The host name, e.g. IP such as 0.0.0.0 for all network adapters or 
        127.0.0.1 for local hosting.
        """
        self._port = port
        "The port at which the server shall be hosted"
        self.ssl_context = flask_ssl_context
        "The SSL context settings"
        self.silent = silent
        "Suppresses output to the logs and to the console"

    @property
    def port(self):
        """
        The network port the server uses
        """
        return self._port

    def add_service(self, service: WebStagService):
        """
        Adds a new service to the server.

        Note that services can only be added to the server before it was
        started.

        :param service: The service to register
        """
        with self._access_lock:
            assert not self._started
            assert service not in self._services
            self._services.append(service)

    def start(self, threaded=False, test=False):
        """
        Starts the server

        :param threaded: Defines if the server shall be started in a background
            thread.
        :param test: Defines if the server shall not be started at all but
            configured for a unit test
        """
        from flask import Flask
        self._flask = Flask(__name__)
        for cur_service in self._services:
            cur_service: WebStagService
            self._flask.register_blueprint(cur_service.service,
                                           **cur_service.reg_params)
        from scistag.webstag.server.flask_server.flask_hosting_thread import \
            FlaskHostingThread
        self.server_thread = FlaskHostingThread(self)
        with self._access_lock:
            self._started = True
        if test:
            return
        if threaded:
            self.server_thread.start()
        else:
            self._run_server()

    @staticmethod
    def _disabled_server_banner(*args, **kwargs):
        """
        Mock for the show_server_banner method to suppress spam to stdout
        """
        pass

    def _setup_logging(self):
        """
        Setups the server's logging behavior
        """
        log = logging.getLogger('werkzeug')
        if self.silent:
            log.setLevel(logging.CRITICAL)
            from flask import cli
            if hasattr(cli, "show_server_banner"):
                cli.show_server_banner = self._disabled_server_banner

    def _run_server(self):
        """
        Executes the server (endless-loop). Do not call this directly.
        """
        self._setup_logging()
        self._flask.run(port=self.port, host=self.host_name,
                        ssl_context=self.ssl_context,
                        debug=False)

    def get_started(self):
        """
        Returns if the server was started
        """
        with self._access_lock:
            return self._started

    def get_handle(self) -> "Flask":
        """
        Returns the server's native handle
        """
        return self._flask
