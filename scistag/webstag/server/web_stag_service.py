"""
Implements the class `WebStagService` which represents a single service
provided by a Flask or FastAPI server.
"""

from __future__ import annotations

from typing import Union

from abc import abstractmethod
from flask import Blueprint

from scistag.webstag.server import WebRequest, WebResponse


class WebStagService:
    """
    Defines a single web service which shall be serverd by the server
    (such as a Blueprint) and it's configuration properties.
    """

    def __init__(self, service_name: str, bp_reg_params: dict | None = None):
        """
        :param service_name: The name under which the service shall be
            registered. Has to be unique.
        :param bp_reg_params: The additional setup parameters to pass to the
            blueprint registration function. (Flask specific)
        """
        self.service: Union["Blueprint", None] = None
        "The service to be registered"
        self.reg_params = bp_reg_params if bp_reg_params is not None else {}
        "Additional registration parameters to be passed to register_blueprint"
        self.service_name = service_name
        "The service's name"

    def set_service_blueprint(self, service: "Blueprint"):
        """
        Assigns a blueprint which will provide this service in flask

        :param service: The blueprint forwarding its requests to us
        """
        self.service = service

    def setup_wrapper_blueprint(self):
        """
        Setups a Flask blueprint for this service which receives all calls
        to the url_suffix root at which this service was registered.

        You can then handle all calls to this base url suffix and via
        the unified handle_unified_request method.
        :return:
        """
        from scistag.webstag.server.flask_server.webstag_service_blueprint import \
            WebStagServiceBlueprint

        blue_print = WebStagServiceBlueprint(self)
        self.set_service_blueprint(blue_print)
        # add routing rules
        blue_print.add_url_rule("/", None, blue_print.execute_service,
                                defaults={'path': ''})
        blue_print.add_url_rule('/<path:path>', None,
                                blue_print.execute_service, )

    def handle_unified_request(self, request: WebRequest) -> WebResponse:
        """
        Receives all calls to this service if
        :meth:`setup_wrapper_blueprint` was used to configure this
        service.

        :param request: The request - unifying incoming Flask and Fast API
            calls.
        :return: The response - which is being converted back to a Flask and/or
            FastAPI response.
        """
        pass
