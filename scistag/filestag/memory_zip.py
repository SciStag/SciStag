"""
Helper class for fast and easy creation of zip files in memory
"""
from __future__ import annotations
import io
import zipfile

from scistag.filestag import FileStag


class MemoryZip(zipfile.ZipFile):
    """
    Helper file for fast and easy zip data creation and extraction in-memory
    """

    def __init__(self, source: str | bytes | None = None, **kwargs):
        """
        :param source: The data source to be loaded to memory. If no
            source is specified (as by default) a new, empty zip archive
            will be created.
        :param kwargs: Additional initializer parameters, see :clasS:
            `zipfile.ZipFile`.
        """
        self._is_closed = False
        if source is not None:
            data = source
            if not isinstance(data, bytes):
                data = FileStag.load(source)
                if data is None:
                    raise ValueError(f"Invalid data source, file not found")
            self._stream = io.BytesIO(data)
            super().__init__(file=self._stream, mode="a", **kwargs)
        else:
            self._stream = io.BytesIO()
            super().__init__(file=self._stream, mode="w", **kwargs)

    def to_bytes(self) -> bytes:
        """
        Closes the zip archive and it's content as bytes

        :return: The zip data
        """
        self.close()
        return self._stream.getvalue()

    def close(self) -> None:
        if self._is_closed:
            return
        self._is_closed = True
        super(MemoryZip, self).close()
