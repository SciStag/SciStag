"""
Defines service specific options if the VisualLog is hosted as web service such as
the IP(s) and port(s) the service is hosted at.
"""

from __future__ import annotations

from scistag.webstag.server_options import ServerOptions


class LogServerOptions(ServerOptions):
    show_urls: bool = True
    """Defines if the URLs at which the server can be reached shall be shown upon 
    start"""

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
        super().validate_options()
