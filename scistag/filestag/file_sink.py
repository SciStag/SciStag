"""
Implements the abstract class :class:`FileSink` which defines the base class
for storage target containers.
"""

from __future__ import annotations

import os

from scistag.filestag import FilePath
from scistag.filestag.protocols import AZURE_PROTOCOL_HEADER, \
    ZIP_SOURCE_PROTOCOL, AZURE_DEFAULT_ENDPOINTS_HEADER


class FileStorageOptions:
    """
    Advanced file storage parameters

    Not yet defined.
    """
    pass


class FileSink:
    """
    A file sink is the abstract base class for a file storage container target,
    eg.g. for storing files in a batch process such as converting a large set
    of images and storing them in an output directory, archive or cloud storage.
    """

    def __init__(self, target: str, **params):
        """
        :param target: The storage target
        :param params: Additional parameters
        """
        self._target = target
        "The sink's storage target"
        self._closed = False
        "Defines if the file sink was finalized (e.g. a zip archive closed)"

    @staticmethod
    def with_target(target: str, **params):
        """
        Creates a file source with given target.

        :param target: The target cloud storage or zip archive at which the data
            shall be stored.

            Supported types (as of now) are:
            - "azure://DefaultEndpoints..." to store data in a
                FileSinkAzureStorage
            - "zip://" w/o a filename to create a memory zip
        :param params: Further parameters to be passed on
        :return: The FileSink instance
        """
        if target == ZIP_SOURCE_PROTOCOL:
            from scistag.filestag.sinks import FileSinkZip
            return FileSinkZip(target=target, **params)
        if target.startswith(AZURE_PROTOCOL_HEADER) or \
                target.startswith(AZURE_DEFAULT_ENDPOINTS_HEADER):
            from .azure.azure_storage_file_sink import AzureStorageFileSink
            return AzureStorageFileSink(target=target, **params)
        if target.startswith("/") or (
                len(target) >= 2 and target[1] == ":") or \
                target.startswith("\\\\"):
            from scistag.filestag.sinks import FileSinkDisk
            if params.get("create_dirs", True):
                FilePath.make_dirs(target)
            return FileSinkDisk(target=target, **params)
        raise ValueError("Unsupported target type")

    def store(self,
              filename: str,
              data: bytes,
              overwrite: bool = True,
              options: FileStorageOptions | None = None) -> bool:
        """
        Stores a single file in the file sink

        :param filename: The file's name
        :param data: The data to be stored
        :param overwrite: Defines if the file may be overwritten if it does
            already exist.
        :param options: Advanced storage and file options
        :return: True on success
        """
        return self._store_int(filename, data, overwrite=overwrite,
                               options=options)

    def _store_int(self,
                   filename: str,
                   data: bytes,
                   overwrite: bool,
                   options: FileStorageOptions | None = None) -> bool:
        """
        The internal storage function to be implemented for the different
        kinds of target types.

        :param filename: The name of the file to be stored
        :param data: The data to be stored
        :param options: Advanced storage and file options
        :return: True on success
        """
        raise NotImplementedError("Missing storage handler implementation")

    def close(self):
        """
        This function should be called when ever you finished adding all files
        to the file sink to finalize it (e.g. a zip archive)

        Alternatively you can create and fill the sink within a `with` block
        such as

        ..  code-block: python:

            with MyFileSink() as fs:
                fs.add("myfile.txt", b"Hello world")
        """
        if self._closed:
            raise AssertionError("Tried to close FileSink twice")
        self._closed = True

    def get_value(self) -> bytes:
        """
        Returns the sink's content as single bytes string.

        This is only supported by a small amount of sinks such as the
        FileSinkZip.

        :return: The sink's data, e.g. the byte stream of a zip archive.
        """
        raise NotImplementedError("Data retrieval function not implemented")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
