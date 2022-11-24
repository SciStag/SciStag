"""
Module defining the basic FileSource and FileSink implementations.
"""

from .file_source_zip import FileSourceZip
from .file_source_disk import FileSourceDisk

__all__ = ["FileSourceZip", "FileSourceDisk"]
