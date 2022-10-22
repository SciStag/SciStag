"""
Provides some low level helper functions for socket communication
"""

from __future__ import annotations


class NetHelper:
    """
    Provides some basic network usage helper functions
    """

    @staticmethod
    def find_free_ports(host_name: str = "0.0.0.0",
                        port_range: tuple[int, int] | None = None,
                        count: int = -1):
        """
        Returns a free TCP/IP port within a given range

        :param host_name: The host name to search at, e.g "localhost" or
            "0.0.0.0" for all adapters.
        :param port_range: The range to search within, from .. to. If no
            range is specified a random port >=1000 will be selected.
        :param count: The count of ports ot return.

            - -1 = return all ports in the search range.
            - count >= 1: Return up to the number of ports
        :return: The list of ports available in that range
        """
        import socket
        from contextlib import closing
        free_ports = []
        if count == 0:
            raise AssertionError("Can not search for zero ports")
        if port_range is None:
            port_range = (0, 0)
        for cur_port in range(port_range[0], port_range[1] + 1):
            with closing(
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                try:
                    s.bind((host_name, cur_port))
                except OSError:
                    continue
                if cur_port == 0:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    free_ports.append(s.getsockname()[1])
                else:
                    free_ports.append(cur_port)
                if count != -1 and len(free_ports) >= count:
                    break
        return free_ports
