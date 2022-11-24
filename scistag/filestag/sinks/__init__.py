"""
Defines the common file sink targets
"""

from .file_sink_disk import FileSinkDisk
from .file_sink_zip import FileSinkZip

__all__ = ["FileSinkDisk", "FileSinkZip"]
