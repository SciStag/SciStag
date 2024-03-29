from __future__ import annotations

from io import BytesIO
import json
import os
from typing import Union

from pydantic import SecretStr

from scistag.filestag.protocols import (
    HTTPS_PROTOCOL_URL_HEADER,
    HTTP_PROTOCOL_URL_HEADER,
    FILE_PATH_PROTOCOL_URL_HEADER,
)
from scistag.webstag import web_fetch

FileSourceTypes = Union[str, SecretStr, bytes]
"""
The file source path.

This can either be a classic local file name path, the path to the URL
of a file or any other protocol supported by FileStag such as
zip://zipFilename/fileNameInZip.
"""

FileTargetTypes = Union[str, SecretStr]
"""
The file target path.

This can either be a classic local file name path, the path to the URL
of a file or any other protocol supported by FileStag such as
zip://zipFilename/fileNameInZip.
"""


class FileStag:
    """
    Helper class to load data from a variety of sources such as local files,
    registered archives of the web
    """

    @classmethod
    def is_simple(cls, filename: FileSourceTypes | FileTargetTypes) -> bool:
        """
        Returns if the file path points to a simple file on disk which does not
        require loading it to memory

        :param filename: The file's source such as a local filename or URL.
            See :class:`FileNameType`
        :return: True if it is a normal, local file
        """
        if isinstance(filename, SecretStr):
            filename = filename.get_secret_value()
        if isinstance(filename, str) and "://" in filename:
            return False
        return True

    @staticmethod
    def resolve_name(path: str | SecretStr | bytes) -> str | bytes:
        """
        Tries to simplify the file name or path

        :param path: The original filename or path
        :return: The simplified name or the original data if invalid type
        """
        if isinstance(path, SecretStr):
            path = path.get_secret_value()
        elif not isinstance(path, str):
            return path
        if path.startswith(FILE_PATH_PROTOCOL_URL_HEADER):
            path = path[len(FILE_PATH_PROTOCOL_URL_HEADER) :]
        return path

    @classmethod
    def load(
        cls, source: FileSourceTypes, as_stream: bool = False, **params
    ) -> bytes | BytesIO | None:
        """
        Loads a file by filename from a local file, a registered web archive
        or the web

        :param source: The file's source such as a local filename or URL.
            See :class:`FileNameType`
        :param params: Advanced loading params passed to the file loader such
            as ``timeout_s`` or ``max_cache_age`` for files from the web.
        :return: The data if the file could be found
        """

        def bundle(result) -> bytes | BytesIO | None:
            """
            Bundles the result as stream if desired

            :param result: The original result
            :return: The result in the desired output format
            """
            if result is not None and as_stream:
                return BytesIO(result)
            return result

        if isinstance(source, bytes):  # pass through
            return bundle(source)
        source = cls.resolve_name(source)
        from .shared_archive import SharedArchive
        from scistag.filestag import ZIP_SOURCE_PROTOCOL

        if source.startswith(ZIP_SOURCE_PROTOCOL):
            return bundle(SharedArchive.load_file(source))
        if source.startswith(HTTP_PROTOCOL_URL_HEADER) or source.startswith(
            HTTPS_PROTOCOL_URL_HEADER
        ):
            return bundle(web_fetch(source, **params))
        if os.path.exists(source):
            return bundle(open(source, "rb").read())
        else:
            return None

    @classmethod
    def save(cls, target: FileTargetTypes, data: bytes, **_) -> bool:
        """
        Saves data to a file

        :param target: The file's target name, see :meth:`load_file`.
        :param data: The data to be stored
        :return: True on success
        """
        if data is None:
            raise ValueError("No data provided")
        target = cls.resolve_name(target)
        if not cls.is_simple(target):
            raise NotImplementedError(
                "At the moment only local file storage" "is supported"
            )
        try:
            with open(target, "wb") as output_file:
                output_file.write(data)
        except (FileNotFoundError, IOError):
            return False
        return True

    @classmethod
    def delete(cls, target: FileTargetTypes, **params) -> bool:

        """
        Deletes a file

        :param target: The file's target name, see :meth:`load_file` for
            the supported protocols.
        :param params: The advanced storage parameters, depending on the
            type of storage, such as timeout_s for file's stored via network.
        :return: True on success
        """
        target = cls.resolve_name(target)
        if not cls.is_simple(target):
            raise NotImplementedError(
                "At the moment only local file deletion" "is supported"
            )
        try:
            os.remove(target)
        except FileNotFoundError:
            return False
        return True

    @classmethod
    def load_text(
        cls,
        source: FileSourceTypes,
        encoding: str = "utf-8",
        crlf: bool | None = None,
        **params,
    ) -> str | None:
        """
        Loads a text file from a given file source

        :param source: The file's source, see :meth:`load_file`.
        :param encoding: The text encoding. utf-8 by default
        :param crlf: Defines if Windows line endings shall be used or suppressed.
            * None = Keep current state
            * False = Linux line endings only (newline)
            * True = Windows line endings only (carriage return, newline)
        :param params: The advanced loading parameters, file source dependent,
            e.g. timeout_s for a timeout from file's from the web.
        :return: The file's content
        """
        source = cls.resolve_name(source)
        data = cls.load(source, **params)
        if data is None:
            return None
        result = data.decode(encoding=encoding)
        if crlf is not None:
            result = result.replace("\r\n", "\n")  # normalize to linux first
            if crlf:
                result = result.replace("\n", "\r\n")
        return result

    @classmethod
    def save_text(
        cls, target: FileTargetTypes, text: str, encoding: str = "utf-8", **params
    ) -> bool:
        """
        Saves text data to a file

        :param target: The file's target, see :meth:`save_file`.
        :param text: The text to be stored
        :param encoding: The encoding to use. utf-8 by default.
        :param params: The advanced storage parameters, depending on the
            type of storage, such as timeout_s for file's stored via network.
        :return: True on success
        """
        if text is None:
            raise ValueError("No data provided")
        target = cls.resolve_name(target)
        encoded_text = text.encode(encoding=encoding)
        return cls.save(target, data=encoded_text, **params)

    @classmethod
    def load_json(
        cls, source: FileSourceTypes, encoding: str = "utf-8", **params
    ) -> dict | None:
        """
        Loads a json dictionary from a given file source

        :param source: The file's source, see :meth:`load_file`.
        :param encoding: The text encoding. utf-8 by default
        :param params: The advanced loading parameters, file source dependent,
            e.g. timeout_s for a timeout from file's from the web.
        :return: The file's content
        """
        source = cls.resolve_name(source)
        data = cls.load(source, **params)
        if data is None:
            return None
        data = data.decode(encoding=encoding)
        return json.loads(data)

    @classmethod
    def save_json(
        cls,
        target: FileTargetTypes,
        data: dict,
        indent: int | None = None,
        encoding: str = "utf-8",
        **params,
    ) -> bool:
        """
        Saves json data to a file target

        :param target: The file's target. See :class:`FileNameType`
        :param data: The dictionary to be stored
        :param indent: The json indenting. None by default
        :param encoding: The encoding to use. utf-8 by default.
        :param params: The advanced storage parameters, depending on the
            type of storage, such as timeout_s for file's stored via network.
        :return: True on success
        """
        if data is None:
            raise ValueError("No data provided")
        target = cls.resolve_name(target)
        text = json.dumps(data) if indent is None else json.dumps(data, indent=indent)
        encoded_text = text.encode(encoding=encoding)
        return cls.save(target, data=encoded_text, **params)

    @classmethod
    def copy(
        cls,
        source: FileSourceTypes,
        target: FileTargetTypes,
        create_dir: bool = False,
        **params,
    ) -> bool:
        """
        Copies a file from given source to given target location

        :param source: The source location
        :param target: The target location
        :param create_dir: Defines if a directory of the target
            shall be created if needed
        :param params: The parameters to be passed to the source loader, e.g.
            max_cache_age etc.
        :return: True on success
        """
        source = cls.resolve_name(source)
        target = cls.resolve_name(target)
        if cls.is_simple(target):
            dirname = os.path.dirname(target)
            if not os.path.exists(dirname):
                if create_dir:
                    os.makedirs(dirname, exist_ok=True)
                else:
                    return False
        data = cls.load(source, **params)
        if data is None:
            return False
        return cls.save(target, data)

    @classmethod
    def exists(cls, filename: FileSourceTypes, **params) -> bool:
        """
        Verifies if a file exists

        :param filename: The file's source such as a local filename or URL.
            See :class:`FileNameType`
        :param params: Advanced parameters, protocol dependent
        :return: True if the file exists
        """
        filename = cls.resolve_name(filename)
        from .shared_archive import SharedArchive
        from scistag.filestag import ZIP_SOURCE_PROTOCOL

        if filename.startswith(ZIP_SOURCE_PROTOCOL):
            return SharedArchive.exists_at_source(filename)
        if filename.startswith(HTTP_PROTOCOL_URL_HEADER) or filename.startswith(
            HTTPS_PROTOCOL_URL_HEADER
        ):
            return web_fetch(filename, **params) is not None
        return os.path.exists(filename)
