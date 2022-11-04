from __future__ import annotations

import json
import os
from typing import Union

from scistag.webstag import web_fetch

HTTPS_PROTOCOL_URL_HEADER = "https://"
"""
Definition for the beginning of a https url to check if a file has to be fetched 
from the web
"""

HTTP_PROTOCOL_URL_HEADER = "http://"
"""
Definition for the beginning of a http url to check if a file has to be fetched 
from the web
"""

FILE_PATH_PROTOCOL_URL_HEADER = "file://"
"Definition for the beginning of a local file url"

FileSourceTypes = Union[str]
"""
The file source path.

This can either be a classic local file name path, the path to the URL
of a file or any other protocol supported by FileStag such as
zip://zipFilename/fileNameInZip.
"""

FileTargetTypes = Union[str]
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
    def is_simple(cls,
                  filename: FileSourceTypes | FileTargetTypes) -> bool:
        """
        Returns if the file path points to a simple file on disk which does not
        require loading it to memory

        :param filename: The file's source such as a local filename or URL.
            See :class:`FileNameType`
        :return: True if it is a normal, local file
        """
        if "://" in filename:
            return False
        return True

    @classmethod
    def load(cls,
             source: FileSourceTypes,
             **params) -> bytes | None:
        """
        Loads a file by filename from a local file, a registered web archive
        or the web

        :param source: The file's source such as a local filename or URL.
            See :class:`FileNameType`
        :param params: Advanced loading params passed to the file loader such
            as ``timeout_s`` or ``max_cache_age`` for files from the web.
        :return: The data if the file could be found
        """
        from .shared_archive import SharedArchive
        from scistag.filestag import ZIP_SOURCE_PROTOCOL
        if source.startswith(FILE_PATH_PROTOCOL_URL_HEADER):
            source = source[len(FILE_PATH_PROTOCOL_URL_HEADER):]
        if source.startswith(ZIP_SOURCE_PROTOCOL):
            return SharedArchive.load_file(source)
        if source.startswith(HTTP_PROTOCOL_URL_HEADER) or source.startswith(
                HTTPS_PROTOCOL_URL_HEADER):
            return web_fetch(source, **params)
        if os.path.exists(source):
            return open(source, "rb").read()
        else:
            return None

    @classmethod
    def save(cls,
             target: FileTargetTypes,
             data: bytes, **params) -> bool:
        """
        Saves data to a file

        :param target: The file's target name, see :meth:`load_file`.
        :param data: The data to be stored
        :param params: The advanced storage parameters, depending on the
            type of storage, such as timeout_s for file's stored via network.
        :return: True on success
        """
        if target.startswith(FILE_PATH_PROTOCOL_URL_HEADER):
            target = target[len(FILE_PATH_PROTOCOL_URL_HEADER):]
        if not cls.is_simple(target):
            raise NotImplementedError("At the moment only local file storage"
                                      "is supported")
        try:
            with open(target, "wb") as output_file:
                output_file.write(data)
        except:
            return False
        return True

    @classmethod
    def delete(cls,
               target: FileTargetTypes,
               **params) -> bool:

        """
        Deletes a file

        :param target: The file's target name, see :meth:`load_file` for
            the supported protocols.
        :param params: The advanced storage parameters, depending on the
            type of storage, such as timeout_s for file's stored via network.
        :return: True on success
        """
        if target.startswith(FILE_PATH_PROTOCOL_URL_HEADER):
            target = target[len(FILE_PATH_PROTOCOL_URL_HEADER):]
        if not cls.is_simple(target):
            raise NotImplementedError("At the moment only local file deletion"
                                      "is supported")
        try:
            os.remove(target)
        except FileNotFoundError:
            return False
        return True

    @classmethod
    def load_text(cls,
                  source: FileSourceTypes,
                  encoding: str = "utf-8",
                  **params) -> str | None:
        """
        Loads a text file from a given file source

        :param source: The file's source, see :meth:`load_file`.
        :param encoding: The text encoding. utf-8 by default
        :param params: The advanced loading parameters, file source dependent,
            e.g. timeout_s for a timeout from file's from the web.
        :return: The file's content
        """
        data = cls.load(source, **params)
        if data is None:
            return None
        return data.decode(encoding=encoding)

    @classmethod
    def save_text(cls,
                  target: FileTargetTypes,
                  text: str,
                  encoding: str = "utf-8",
                  **params) -> bool:
        """
        Saves text data to a file

        :param target: The file's target, see :meth:`save_file`.
        :param text: The text to be stored
        :param encoding: The encoding to use. utf-8 by default.
        :param params: The advanced storage parameters, depending on the
            type of storage, such as timeout_s for file's stored via network.
        :return: True on success
        """
        encoded_text = text.encode(encoding=encoding)
        return cls.save(target, data=encoded_text, **params)

    @classmethod
    def load_json(cls,
                  source: FileSourceTypes,
                  encoding: str = "utf-8",
                  **params) -> dict | None:
        """
        Loads a json dictionary from a given file source

        :param source: The file's source, see :meth:`load_file`.
        :param encoding: The text encoding. utf-8 by default
        :param params: The advanced loading parameters, file source dependent,
            e.g. timeout_s for a timeout from file's from the web.
        :return: The file's content
        """
        data = cls.load(source, **params)
        if data is None:
            return None
        data = data.decode(encoding=encoding)
        return json.loads(data)

    @classmethod
    def save_json(cls,
                  target: FileTargetTypes,
                  data: dict,
                  indent: int | None = None,
                  encoding: str = "utf-8",
                  **params) -> bool:
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
        text = json.dumps(data) if indent is None else json.dumps(data,
                                                                  indent=indent)
        encoded_text = text.encode(encoding=encoding)
        return cls.save(target, data=encoded_text, **params)

    @classmethod
    def copy(cls, source: str, target: str, create_dir: bool = False,
             **params) -> bool:
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
    def exists(cls,
               filename: FileSourceTypes, **params) -> bool:
        """
        Verifies if a file exists

        :param filename: The file's source such as a local filename or URL.
            See :class:`FileNameType`
        :param params: Advanced parameters, protocol dependent
        :return: True if the file exists
        """
        from .shared_archive import SharedArchive
        from scistag.filestag import ZIP_SOURCE_PROTOCOL
        if filename.startswith(FILE_PATH_PROTOCOL_URL_HEADER):
            filename = filename[len(FILE_PATH_PROTOCOL_URL_HEADER):]
        if filename.startswith(ZIP_SOURCE_PROTOCOL):
            return SharedArchive.exists_at_source(filename)
        if filename.startswith(HTTP_PROTOCOL_URL_HEADER) or filename.startswith(
                HTTPS_PROTOCOL_URL_HEADER):
            return web_fetch(filename, **params) is not None
        return os.path.exists(filename)
