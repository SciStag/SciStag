from __future__ import annotations
import io
import os
import zipfile
from multiprocessing import RLock
import fnmatch

from scistag.filestag.protocols import ZIP_SOURCE_PROTOCOL


class SharedArchive:
    """
    Defines a shared zip archive which can be used by multiple users, e.g. classes to provide shared data quickly from a
    compact archive once initialized.

    Usage:
    SharedArchive.register("sharedData.zip", "sharedData")

    Then data can be loaded flexible via FileStag, independent of if it's located in the web, in a zip archive or
    as simple local file:
    FileStag.load_file("zip://@sharedData/testFile.zip")
    FileStag.load_file("local_file.txt")
    FileStag.load_file("https://www....")

    Note: Registered zip files have to add an @ in front of their identifier.
    """

    access_lock = RLock()
    "Multithreading access lock"
    archives: dict[str, "SharedArchive"] = {}
    "Dictionary of the loaded archives, identifier: SharedArchive"

    def __init__(self, source: str | bytes, identifier: str, cache=False):
        """
        Initializer

        :param source: The source, either a filename or a bytes object
        :param identifier: The identifier via which this object can be accessed
        :param cache: Defines if this archive shall be cached in memory
        """
        self.identifier = identifier
        "The archive's unique identifier"
        self.access_lock = RLock()
        "Access lock (for multi-threading)"
        self.filename = ""
        "The archive's filename (if loaded from a file), otherwise empty"
        if isinstance(source, str):
            self.filename = os.path.normpath(source)
            if cache:
                with open(source, "rb") as source_file:
                    source = io.BytesIO(source_file.read())
        elif isinstance(source, bytes):
            source = io.BytesIO(source)
        self.zip_file = zipfile.ZipFile(source)

    def close(self):
        """
        Closes the archive to unload and not having to wait for the gc
        """
        if self.zip_file is not None:
            self.zip_file.close()
            self.zip_file = None

    def find_files(self, name_filter: str = "*") -> list[str]:
        """
        Lists all element from the archive matching given filter

        :param name_filter: The filter
        :return: The list of found elements
        """
        with self.access_lock:
            elements = [
                element.filename
                for element in self.zip_file.filelist
                if fnmatch.fnmatch(element.filename, name_filter)
            ]
            return elements

    def exists(self, name: str) -> bool:
        """
        Returns if the file exists

        :param name: The file's name
        :return: True if it exists
        """
        with self.access_lock:
            return name in self.zip_file.namelist()

    def read_file(self, name: str) -> bytes | None:
        """
        Loads the data from given file to memory

        :param name: The name of the file to load
        :return: The file's data. None if the file could not be found
        """
        with self.access_lock:
            if name not in self.zip_file.namelist():
                return None
            return self.zip_file.open(name, "r").read()

    @classmethod
    def register(
        cls, source: str | bytes, identifier: str, cache=False
    ) -> "SharedArchive":
        """
        Registers a new archive.

        :param source: The source, either a filename or a bytes object
        :param identifier: The identifier via which this object can be accessed
        :param cache: Defines if this archive shall be cached in memory
        :return: The archive
        """
        assert len(identifier)
        with cls.access_lock:
            if identifier in cls.archives:
                return cls.archives[identifier]
            new_archive = SharedArchive(source, identifier, cache)
            cls.archives[identifier] = new_archive
            return new_archive

    @classmethod
    def exists_at_source(cls, identifier: str, filename: str | None = None) -> bool:
        """
        Returns if given file exists

        :param identifier: The archive identifier. Alternate: a full identifier
            in the form
        zip://@identifier/filename
        :param filename: The name of the file to load.
        :return: True if the file exists
        """
        archive: SharedArchive | None = None
        if identifier.startswith(ZIP_SOURCE_PROTOCOL):
            identifier, filename = cls._split_identifier_and_filename(identifier)
            if identifier.endswith(".zip"):
                return cls.check_in_zip_direct(identifier, filename)
        with cls.access_lock:
            if identifier in cls.archives:
                archive = cls.archives[identifier]
        if archive is None:
            return False
        archive: SharedArchive
        return archive.exists(filename)

    @classmethod
    def load_file(cls, identifier: str, filename: str | None = None) -> bytes | None:
        """
        Loads a file by filename

        :param identifier: The archive identifier. Alternate: a full identifier
            in the form
        zip://@identifier/filename or a path to a zipfile, e.g.
            zip://filename.zip/filename
        :param filename: The name of the file to load.
        :return: The data if the file could be found
        """
        archive: SharedArchive | None = None
        if identifier.startswith(ZIP_SOURCE_PROTOCOL):
            identifier, filename = cls._split_identifier_and_filename(identifier)
            if identifier.endswith(".zip"):
                return cls.load_file_from_zip_direct(identifier, filename)
        with cls.access_lock:
            if identifier in cls.archives:
                archive = cls.archives[identifier]
        if archive is None:
            return None
        archive: SharedArchive
        return archive.read_file(filename)

    @classmethod
    def scan(
        cls, identifier: str, name_filter: str = "*", long_identifier=True
    ) -> list[str]:
        """
        Scans an archive for a given file mask to search for files of a specific
        type

        :param identifier: The archive identifier
        :param name_filter: The name mask to search for
        :param long_identifier: Defines if the scan shall return long
            identifiers
            (zip://@identifier/filename) so the results can be used for
            FileStag.load_file). True by default.
        :return: All file in given archive matching the mask
        """
        if identifier.startswith(ZIP_SOURCE_PROTOCOL):
            identifier = identifier[len(ZIP_SOURCE_PROTOCOL) :]
            identifier = identifier.lstrip("@").rstrip("/")
        archive: SharedArchive | None = None
        with cls.access_lock:
            if identifier in cls.archives:
                archive = cls.archives[identifier]
        if archive is None:
            return []
        archive: SharedArchive
        results = archive.find_files(name_filter)
        if long_identifier:
            results = [
                f"{ZIP_SOURCE_PROTOCOL}@{identifier}/{element}" for element in results
            ]
        return results

    @classmethod
    def is_loaded(cls, filename) -> bool:
        """
        Returns if a given zip file was registered

        :param filename: The zip file to be removed
        :return: True if the archive exists
        """
        with cls.access_lock:
            for identifier, archive in cls.archives.items():
                archive: SharedArchive
                if filename == archive.filename:
                    return True
        return False

    @classmethod
    def unload(cls, filename: str | None = None, identifier: str | None = None) -> bool:
        """
        Unloads a zip file, e.g. if it's uninstalled

        :param filename: The zip file to be removed
        :param identifier: The identifier of the archive to unload
        :return: True if an archive with given filename could be found and
            removed
        """
        with cls.access_lock:
            for cur_identifier, archive in cls.archives.items():
                archive: SharedArchive
                if (
                    filename is not None
                    and filename == archive.filename
                    or identifier is not None
                    and cur_identifier == identifier
                ):
                    cls.archives[cur_identifier].close()
                    del cls.archives[cur_identifier]
                    return True
        return False

    @staticmethod
    def load_file_from_zip_direct(zip_filename, filename) -> bytes | None:
        """
        Loads a file directly from a zip archive

        :param zip_filename: The name of the zip file
        :param filename: The filename within the zip file
        :return: The file's data if it could be found. None otherwise.
        """
        with zipfile.ZipFile(zip_filename, "r") as zip_file:
            return zip_file.read(filename)

    @staticmethod
    def check_in_zip_direct(zip_filename, filename) -> bool:
        """
        Verifies if a file exists within a zip file

        :param zip_filename: The name of the zip file
        :param filename: The filename within the zip file
        :return: Returns if the file exists
        """
        with zipfile.ZipFile(zip_filename, "r") as zip_file:
            return filename in zip_file.namelist()

    @classmethod
    def _split_identifier_and_filename(cls, identifier) -> (str, str):
        """
        Returns the registered zip archive and the filename within the archive

        :param identifier: The provided identifier
        :return: identifier or filename of zip file, filename within the archive
        """
        identifier = identifier[len(ZIP_SOURCE_PROTOCOL) :]
        if not identifier.startswith("@"):
            identifier_elements = identifier.split(".zip/")
            if len(identifier_elements) < 2:
                raise ValueError(
                    "You need to pass the zip's filename followed by a slash "
                    "and the name of the"
                    "file within the zip archive."
                )
            archive_name, filename_in_zip = identifier_elements[0:2]
            archive_name += ".zip"
            return archive_name, filename_in_zip
        if "/" not in identifier:
            raise ValueError("No filename provided. Form: zip://@identifier/filename")
        slash_index = identifier.index("/")
        filename = identifier[slash_index + 1 :].lstrip("/")
        identifier = identifier[1:slash_index]
        return identifier, filename


__all__ = ["SharedArchive"]
