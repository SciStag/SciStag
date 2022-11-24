"""
Implements the class :class:`ArchiveFileSinkProto` which defines the common
base class for all FileSinks which are able to summarize their whole content
to a single byte stream.
"""

from __future__ import annotations

from scistag.filestag import FileSink, FileStorageOptions


class ArchiveFileSinkProto(FileSink):
    """
    The archive file sink is an abstract base class for FileSinks which are
    able to summarize their content in a single byte stream and are thus
    for example capable of bundling data batch-wise e.g. to upload them to
    the cloud.

    Do not use this class directly. if you want to collect files in a zip
    archive use FileSinkZip.

    ..  code-block: Python

        with FileSinkZip() as fs:
            fs.store("file1.bin", data)
            fs.store("file1.bin", data)
            fs.store("file1.bin", data)
            ...
        send_data_to_cloud(fs.get_data())
    """

    def __init__(self, target: str, **params):
        """
        :param target: The sink's storage target
        :param params: Additional initializer parameters. See :class:`FileSink`.
        """
        super().__init__(target=target, **params)

    def _store_int(self,
                   filename: str,
                   data: bytes,
                   overwrite: bool,
                   options: FileStorageOptions | None = None) -> bool:
        raise NotImplementedError("Storage method not implemented")
