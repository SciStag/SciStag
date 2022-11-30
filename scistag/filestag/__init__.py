"""
The FileStag modules provides helper functions and classes for scanning
directories, storing files and receiving files from zip archives or the
cloud as well as serializing and deserializing data.
"""

from .shared_archive import SharedArchive
from .protocols import ZIP_SOURCE_PROTOCOL
from .file_stag import FileStag, FileSourceTypes
from .file_path import FilePath
from .file_source import FileSource
from .file_observer import FileObserver
from .file_sink import FileSink, FileStorageOptions
from .memory_zip import MemoryZip
from .bundle import Bundle

__all__ = ["SharedArchive", "FileStag", "FileSource", "FileSourceTypes",
           "FilePath", "Bundle", "FileSink", "FileStorageOptions",
           "FileObserver", "MemoryZip"]
