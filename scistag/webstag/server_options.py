"""
Defines the high-level configuration for a web server
"""

from __future__ import annotations

from typing import Union

from pydantic import BaseModel, Field


class ServerOptions(BaseModel):
    """
    Server specific configuration options
    """

    server_logs: bool = False
    """Defines if the Flask and/or FastAPI logs shall be enabled."""
    host_name: str = "127.0.0.1"
    """
    The IP(s) to listen at.

        - 127.0.0.1 = Local access only (default) as
          "there is no place like localhost".
        - "0.0.0.0" = Listen at all local network adapters"""
    port: Union[int, tuple[int, int]] = 8010
    """The port ot listen at or a port range to select the first port within. 
    8010 by default. 0 for a random port."""
    public_ips: Union[str, list[str], None] = None
    """If you run the service on a virtual machine in the cloud you can pass its public 
    IPs to log the correct connection URls to the console. If you pass "auto" as ip the 
    public IP will be auto-detected via ipify."""
    url_prefix: str = ""
    """
    The url prefix at which the service shall be hosted.
        "" = At https://server
        "log/" = At https://server/"""
    arguments: dict = Field(default_factory=dict)
    """Additional, API specific (Flask or FastAPI) server argument options which shall
     be passed into the initializer"""

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """

    def setup_server_defaults(
        self, port: int | tuple[int | int] | None = None, detect_public_ip=True
    ):
        """
        Setups this system as server using host 0.0.0.0 and a public IP
        :param port: The server's port or port range
        :param detect_public_ip: Defines if the server's public ip shall be detected
        :return: Self
        """
        if port is not None:
            self.port = port
        self.host_name = "0.0.0.0"
        if detect_public_ip:
            if self.public_ips is None:
                self.public_ips = []
            self.public_ips.append("auto")
        return self
