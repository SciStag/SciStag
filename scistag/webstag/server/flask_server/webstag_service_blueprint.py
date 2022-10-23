"""
Flask wrapper from a generalized WebStagService to a Flask Blueprint
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from flask import Blueprint, request, Response

from scistag.webstag.server import WebRequest, WebResponse

if TYPE_CHECKING:
    from scistag.webstag.server.web_stag_service import WebStagService


class WebStagServiceBlueprint(Blueprint):
    """
    Blueprint wrapper for Flask which forwards all incoming requests to its
    WebStagClassService.
    """

    def __init__(self, service: "WebStagService"):
        """
        :param service: Defines the service to which all Flask requests of this
            blueprint shall be foearded.
        """
        super().__init__(service.service_name, __name__)
        self.service = service

    def execute_service(self, path):
        """
        This function is called directly from flask and forwards them to
        our API independent handler.

        It collects all relevant information such as method, headers etc.
        and bundles them in a web request.

        :param path:
        :return: The Flask response
        """
        cr = request
        fw_request = WebRequest(path=path, method=cr.method,
                                headers=dict(cr.headers),
                                body=None,
                                parameters=dict(cr.args), relative_path=path,
                                base_url=cr.base_url,
                                url=cr.url,
                                host_url=cr.host_url,
                                url_root=cr.url_root,
                                remote_addr=cr.remote_addr,
                                environ=cr.environ,
                                mimetype=cr.mimetype,
                                host=cr.host
                                )
        w_response: WebResponse = self.service.handle_unified_request(fw_request)
        r = Response(w_response.body, status=w_response.status)
        if not w_response.cache:
            r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            r.headers["Pragma"] = "no-cache"
            r.headers["Expires"] = "0"
            r.headers['Cache-Control'] = 'public, max-age=0'
        return r
