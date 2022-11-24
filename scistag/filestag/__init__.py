"""
The FileStag modules provides helper functions and classes for scanning
directories, storing files and receiving files from zip archives or the
cloud as well as serializing and deserializing data.
"""

from .shared_archive import SharedArchive
from .protocols import ZIP_SOURCE_PROTOCOL
from .file_stag import FileStag
from .file_path import FilePath
from .file_source import FileSource
from .file_source_observer import FileSourceObserver
from .file_sink import FileSink, FileStorageOptions
from .memory_zip import MemoryZip
from .bundle import Bundle

__all__ = ["SharedArchive", "FileStag", "FileSource",
           "FilePath", "Bundle", "FileSink", "FileStorageOptions",
           "FileSourceObserver", "MemoryZip"]
