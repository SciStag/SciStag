"""
Implements the class :class:`SystemInfo` and provides general information
about the system
"""

import platform
from enum import IntEnum

USING_WINDOWS = (
    "CYGWIN" in platform.system().upper() or "WINDOWS" in platform.system().upper()
)
"Defines if we are using Windows"
USING_OSX = "DARIN" in platform.system().upper()
"Defines if we are using OS X"


class OSTypes(IntEnum):
    """
    Enumeration of operating system types
    """

    WINDOWS = 1
    "This operating system is Windows based"
    LINUX = 2
    "This operating system is Linux based"
    OSX = 3
    "This operating system is OSX based"

    @property
    def is_windows(self) -> bool:
        """
        Returns if this is a Windows based OS
        """
        return self.value == self.WINDOWS

    @property
    def identifier(self) -> str:
        """
        Returns the OS name as identifier
        """
        names = {
            self.WINDOWS.value: "windows",
            self.OSX.value: "osx",
            self.LINUX.value: "linux",
        }
        return names[self.value]


class SystemInfo:
    """
    Provides general information about the system
    """

    os_type = (
        OSTypes(OSTypes.WINDOWS)
        if USING_WINDOWS
        else (OSTypes(OSTypes.OSX) if USING_OSX else OSTypes(OSTypes.LINUX))
    )
    "Defines which operating system is being used"
