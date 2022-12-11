"""
Provides a set of common helper functions for building solutions for the WWW
"""
from __future__ import annotations

ONE_DAY = 24.0 * 60.0 * 60.0
"Default time for caching the IP resolving"


class WebHelper:
    """
    Helper function for resolving host ips and then own IP
    """

    @staticmethod
    def get_public_ip(timeout_s=5.0, max_cache_age=ONE_DAY) -> str | None:
        """
        Returns the server's public IP as seen by other servers by using
        the IP resolving service defined. (at the moment limited to ipify).

        :param timeout_s: The maximum response timeout in seconds
        :param max_cache_age: The time in seconds for how long the result
            shall be cached.
        :return: The IP
        """
        from scistag.webstag.web_fetch import web_fetch

        api_url = "https://api.ipify.org"
        result = web_fetch(api_url, max_cache_age=max_cache_age, timeout_s=timeout_s)
        if result is None:
            return None
        return result.decode("utf8")
