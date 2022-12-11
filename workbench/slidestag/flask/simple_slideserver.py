from __future__ import annotations


class SimpleSlideServer:
    """
    A very simplistic Flask server setup to make your SlideStag application accessible with just two lines of code
    """

    @staticmethod
    def run_simple_server(
        host_name: str = "0.0.0.0",
        port: int = 5020,
        ssl_context: tuple[str, str] | None = None,
        blueprints: list | None = None,
    ):
        """
        Setups a server and starts it

        :param host_name: The server host IP, e.g. 127.0.0.1 or 0.0.0.0 for local or local network hosting
        :param port: The port at which the application shall be hosted. 5020 by default.
        :param ssl_context: The SSL context (filename of the SSL certificate and filename of the key) to provide the
        service via https.
        :param blueprints: Additional blue prints to register. Tuples are interpreted in the form blueprint, urlprefix
        :return:
        """
        from flask import Flask
        from werkzeug.serving import WSGIRequestHandler
        import logging
        from scistag.slidestag4flask import slidestag_service

        new_app = Flask(
            __name__,
            static_url_path="",
            static_folder="web/static",
            template_folder="web/templates",
        )
        new_app.register_blueprint(slidestag_service)
        if blueprints is not None:  # register additional blueprints
            for element in blueprints:
                if isinstance(element, tuple):
                    new_app.register_blueprint(element[0], url_prefix=element[1])
                else:
                    new_app.register_blueprint(element)
        app = new_app
        WSGIRequestHandler.protocol_version = "HTTP/1.1"
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)
        app.run(port=port, host=host_name, ssl_context=ssl_context)
