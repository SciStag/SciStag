"""
Implements the :class:`FileSource` class and it's essential helper classes.

The FileSource class lets you easily iterate through large amounts of files
stored locally, on disk, in zip archives, in cloud storages and even zip
archives in cloud storages.
"""

from __future__ import annotations

import io
import os
from abc import abstractmethod
from collections import Counter
from datetime import datetime
from fnmatch import fnmatch
from hashlib import md5
from typing import Callable, Any, TYPE_CHECKING, Union

from pydantic import BaseModel, SecretStr

from scistag.filestag.bundle import Bundle
from scistag.filestag.file_source_iterator import FileSourceIterator, \
    FileIterationData, FilterCallback
from scistag.filestag.protocols import AZURE_PROTOCOL_HEADER, \
    AZURE_DEFAULT_ENDPOINTS_HEADER
from scistag.filestag.file_stag import FileStag

CACHE_VERSION = "cache_version"

if TYPE_CHECKING:
    import pandas as pd


class FileSourceElement:
    """
    Provides the data of a single file returned from a :class:`FileSource`
    """

    def __init__(self, data: bytes, name: str):
        """
        :param data: The file's content
        """
        self.data = data
        "Holds the file's data"
        self.filename = name
        "The file's name. Usually relative to it's search path"


class FileSourcePathOptions:
    """
    Defines the options for accessing a files full path
    """

    def __init__(self, for_file_stag=False):
        """
        :param for_file_stag: Defines if also return values are valid which
            can just be used internally, such as azure:// for Azure resources
            or zip:// for content in zip files. False by default.
        """
        self.for_file_stag = for_file_stag
        """
        Defines if also FileStag-only compatible return paths are allowed
        which can just be used within SciStag via e.g. :meth:`FileStag.load`.
        """


class FileListEntry(BaseModel):
    """
    Defines a single entry in the file list
    """
    filename: str
    "The file's name"
    file_size: int = 0
    "The file's size in bytes"
    created: datetime = datetime.now()
    "The element's creation time"
    modified: datetime = datetime.now()
    "The element's last modification time"


class FileListModel(BaseModel):
    """
    Defines a list of files storable in a database
    """
    user_version = 1
    """
    The user definable version number. If the version of the stored data does
    not match the one passed, the list is considered being invalid
    """
    format_version: int = 1
    """
    The format version
    """
    files: list[FileListEntry]
    """
    The file data
    """


FileList = list[FileListEntry]


class FileSource:
    """
    Base class for an iterable file source to batch process file lists such as
    directories, zip archives or cloud storages at small and large scale using
    a unified interface.
    """

    # noinspection PyUnusedLocal
    def __init__(self, search_mask: str = "*",
                 search_path: str = "",
                 recursive: bool = True,
                 filter_callback: FilterCallback | None = None,
                 index_filter: tuple[int, int] | None = None,
                 fetch_file_list: bool = True,
                 max_file_count: int = -1,
                 file_list_name: str | tuple[str, int] | None = None,
                 max_web_cache_age: float = 0.0,
                 dont_load=False,
                 sorting_callback: Callable[
                                       [FileListEntry], Any] | None = None):
        """
        For a detailed parameter description see :meth:`from_path`
        """
        self.search_mask = search_mask
        """
        The search mask to match the filenames against before they are returned
        """
        self.search_path = search_path
        "The path to search within, e.g. a file path"
        self.recursive = recursive
        "Defines if the search shall be executed recursive"
        self.filter_callback = filter_callback
        """
        The filter function which will be called for each file to verify if it 
        shall be processed
        """
        self.user_data = {}
        "The user data for further customization, e.g. of the filter callback"
        self.index_filter: tuple[int, int] | None = index_filter
        """
        The index filter helps splitting a processing task to multiple, 
        threads nodes and/or processes.
        
        See initializer parameter.
        """
        self._file_list: FileList | None = None
        """
        A sorted list of all to files (if available e.g. by setting
         fetch_file_list=True).
        
        Note that settings such as :attr:`index_filter` and 
        :attr:`max_file_count` have no effect on the file_list by default. 
        You can though explicitly call the method :meth:`reduce_file_list` which 
        will execute all filters in advance to provide you the final file_list 
        and will disable these variable afterwards.
        """
        self._file_set = None
        """
        A set containing all known files. Only valid if file_list is available 
        too
        """
        self.output_filename_list: list[str] | None = None
        """
        If defined it provides the output filenames for every file in 
        self.file_list.
        """
        self.max_file_count = max_file_count
        """
        The maximum number of files to process. (excluding the impact of 
        :attr:`index_filter`
        """
        self.is_closed = False
        "Defines if this file source was closed"
        self._statistics: dict | None = None
        "The statistics, only available when all files were iterated"
        self.dont_load = dont_load
        """
        If set to true the iterator ``for element in FileSource`` will not
        fetch the file's content but just iterate through it's filenames
        """
        self._file_list_name = None
        "The name of the file from which the file list shall be loaded"
        self._file_list_version: int = -1
        """
        The version of the file list to assume. If it mismatches the
        stored version it will be replaced
        """
        self.sorting_callback = sorting_callback
        if sorting_callback is not None and not fetch_file_list:
            raise ValueError("Sorting is only supported in combination w/"
                             " fetch_file_list=True")
        """
        A function to be called (and pass into sorted) to sort the file list
        before it's stored.
        """
        if file_list_name is not None:
            if isinstance(file_list_name, tuple):
                self._file_list_name, self._file_list_version = file_list_name
            else:
                self._file_list_name = file_list_name
        self.max_web_cache_age = max_web_cache_age

    @staticmethod
    def from_source(source: str | bytes | SecretStr,
                    search_mask: str = "*",
                    search_path: str = "",
                    recursive: bool = True,
                    filter_callback: FilterCallback | None = None,
                    sorting_callback: \
                            Callable[[FileListEntry], Any] | None = None,
                    index_filter: tuple[int, int] | None = None,
                    fetch_file_list: bool = True,
                    max_file_count: int = -1,
                    file_list_name: str | tuple[str, int] | None = None,
                    max_web_cache_age: float = 0.0,
                    dont_load=False) -> FileSource | None:
        """
        Auto-detects the required FileSource implementation for a given source
        path

        :param source: The path you would like to iterate. The following path
            types are currently supported:
            * /home/aDirectory: Will return a FileSourceDisk object to iterate
                through a directory's content
            * /home/myZipArchive.zip: Will return a FileSourceZip object to
                iterate through a zip archive
            * azure://DefaultEndpointsProtocol=https;AccountName=...;AccountKey=.../container/path:
                Will iterate to an Azure Blob Storage.
            * A bytes object: Detects the source type and opens it. At the
                moment only zip archive data ia supported.

            For more secure handling of connection strings with key you can
            also pass a SecretStr.
        :param search_mask: The file name filter mask
        :param search_path: The search path, e.g. directory name or relative
            path to the zip root, storage root etc.
        :param recursive: Defines if the search shall be executed recursive.
            True by default.
        :param filter_callback: A callback function to call for each file to
            verify if it shall be processed or ignored.
            See :const:`FilterCallback`
        :param sorting_callback:
            A function to be called (and pass into sorted) to sort the file list
            before it is stored.

            Is called for every element and has to return the sorting value,
            either a string, float or another size comparable data type.

            Does only work in combination with fetch_file_list.
        :param index_filter: The index filter helps splitting a processing task
            to multiple, threads nodes and/or processes.

            The first tuple element defines the total worker count, the second
            tuple element the current worker index (0 .. worker_count-1).
            If you want to for example process a zip archive by 4 threads in
            parallel just spawn 4 threads and pass (4,0) to the first, (4,1)
            to the second (4,2) to the third and (4,3) to the third.

            All four threads can then work in parallel and store their processed
            data parallel into one or multiple  FileSinks which are (at least in
             most cases) multi-thread safe.
        :param fetch_file_list: If set to true the FileSource will try to
            iterate all filenames in advance. True by default.

            This is recommended especially if you are using sources where it's
            not guaranteed that the file names will always be provided in the
            same order and you intend to share a task among multiple threads to
            guarantee a consistent behavior.
        :param file_list_name: If provided the file list be cached in the
            file name passed. This makes working with large directories or
            cloud storages much faster.

            You can either pass a string, just containing the file name or a
            tuple of (filename, version) so you can enforce replacing the list
            when ever you pass a new version number.
        :param max_file_count: The maximum number of files to process (excluding
            the index filter's impact)
        :param max_web_cache_age: The count of seconds for how long files from
            this source may be stored and received from the cache if this
            source is remote, e.g. Azure, AWS.
        :param dont_load: If set to true the iterator will not provide the
            file's content but just iterate the filenames. Helpful if the
            consumer for example requires a path to files stored on disk.
        :return: The FileSource implementation for your path. None if the path
            can not be identified.
        """
        params = {"search_mask": search_mask,
                  "search_path": search_path,
                  "recursive": recursive,
                  "filter_callback": filter_callback,
                  "index_filter": index_filter,
                  "fetch_file_list": fetch_file_list,
                  "file_list_name": file_list_name,
                  "max_web_cache_age": max_web_cache_age,
                  "max_file_count": max_file_count,
                  "sorting_callback": sorting_callback,
                  "dont_load": dont_load}
        if isinstance(source, SecretStr):
            source = source.get_secret_value()
        if isinstance(source, bytes):
            from scistag.filestag.sources.file_source_zip import FileSourceZip
            return FileSourceZip(source=source, **params)
        if source.startswith(AZURE_PROTOCOL_HEADER) or \
                source.startswith(AZURE_DEFAULT_ENDPOINTS_HEADER):
            from scistag.filestag.azure.azure_storage_file_source import \
                AzureStorageFileSource
            return AzureStorageFileSource(source=source, **params)
        if not (source.endswith("/") or source.endswith(
                "\\")) and source.endswith(".zip"):
            from scistag.filestag.sources.file_source_zip import FileSourceZip
            return FileSourceZip(source=source, **params)
        if source.__contains__("://"):
            raise NotImplementedError("Unknown protocol for FileSource")
        from scistag.filestag.sources.file_source_disk import FileSourceDisk
        return FileSourceDisk(path=source, **params)

    def refresh(self):
        """
        Refreshes the file list
        """
        if self._file_list is not None:
            del self._file_list
        self._file_list = None
        if self._file_set is not None:
            del self._file_set
        self._file_set = None
        self._create_file_list_int(no_cache=True)

    def get_hash(self, max_content_size: int = 0):
        """
        Creates a hash of the current file list to detect potential
        modifications of the files. By default this hash is created using
        the file sizes and file time stamps. If desired the hash can
        also be created using the file's content.

        :param max_content_size: The maximum size of a file to compute up to
            which it's hash is directly computed from its content.
        :return: The MD5 hash
        """
        stream = io.BytesIO()
        for cur_file in self.get_file_list():
            stream.write(
                cur_file.filename.__hash__().to_bytes(8, "little", signed=True))
            stream.write(cur_file.file_size.to_bytes(8, "little", signed=True))
            stream.write(
                cur_file.created.__hash__().to_bytes(8, "little", signed=True))
            stream.write(
                cur_file.modified.__hash__().to_bytes(8, "little", signed=True))
            if max_content_size > 0 and cur_file.file_size <= max_content_size:
                stream.write(
                    md5(self.read_file(cur_file.filename)).hexdigest().encode(
                        "utf-8"))
        return md5(stream.getvalue()).hexdigest()

    def __hash__(self):
        return self.get_hash(max_content_size=0)

    @abstractmethod
    def _get_source_identifier(self) -> str:
        """
        Has to return a unique identifier for this file source which
        identifies the name of this source in the cache database.

        Can for example be the search path and the search mask or parts of the
        connection string.

        :return: The unique identifier
        """
        return ""

    def get_file_list(self) -> FileList | None:
        """
        Returns the file list (if available).

        Note that the file list is not available for all file sources.
        Pass fetch_file_list = true to the initializer of all supported
        FileSources to fetch the list in advance.

        :return: The list of filenames and their size (so far known).
        """
        return self._file_list

    def get_file_list_as_df(self) -> "pd.DataFrame":
        """
        Returns the file list as dataframe

        :return: The file list
        """
        file_list = [entry.dict() for entry in self._file_list]
        import pandas as pd
        return pd.DataFrame(file_list)

    def encode_file_list(self, version: int = -1) -> bytes:
        """
        Encodes the file list so it can be stored on disk

        :param version: The user defined version number. It can be passed
            to enforce updating the list when ever this number is changed.

            If -1 is passed the version is ignored.
        :return: The encoded file list
        """
        df = self.get_file_list_as_df()
        data = Bundle.bundle(
            {"version": 1, "data": df, CACHE_VERSION: version}, compression=0)
        return data

    def load_file_list(self, source: bytes | str, version: int = -1) -> bool:
        """
        Tries to load the file list from file

        :param source: The file list source. Any FileStag compatible data
            source.
        :param version: The user defined version number. It can be passed
            to enforce updating the list when ever this number is changed.

            If -1 is passed the version is ignored.
        :return: True if a valid list could be loaded.
        """
        if not isinstance(source, bytes):
            source = FileStag.load(source)
        if source is None:
            return False
        data = Bundle.unpack(source)
        assert isinstance(data, dict) and data.get("version") == 1
        if version != -1 and data.get(CACHE_VERSION, -1) != version:
            return False
        df: "pd.DataFrame" = data['data']
        key_list = df.columns.to_list()
        self.update_file_list([
            FileListEntry.parse_obj(dict(zip(key_list, cur_element))) for
            cur_element in df.itertuples(index=False, name=None)
        ], may_sort=False)
        return True

    def save_file_list(self, target: str, version: int = -1):
        """
        Saves the file list to a file so it can be quickly restored after
        a restart of the application.

        :param target: The FileStag compatible file target, e.g. a local file
            name
        :param version: The user defined version number. It can be passed
            to enforce updating the list when ever this number is changed.

            If -1 is passed the version is ignored.
        """
        FileStag.save(target, self.encode_file_list(version=version))

    def set_file_list(self, new_list: list[str] | list[FileListEntry]):
        """
        Sets a custom file list provided by the user.

        Helpful for large jobs where the total file list is split into
        several working packages in advance and the shares need to be
        customized.

        :param new_list: The new list to be assigned. Either a list of
            "FileListEntry"s with all details or a list of filenames
        """
        if len(new_list) and isinstance(new_list[0], str):
            lst = [FileListEntry(filename=element, file_size=-1) for element in
                   new_list]
        else:
            lst = new_list
        self.update_file_list(lst)

    def get_absolute(self, filename: str,
                     options: FileSourcePathOptions | None = None) -> \
            str | None:
        """
        Returns the full path to the resource if possible, e.g. the absolute
        path to a file on disk in case of an FileSourceDisk element.

        :param filename: The name of the file of which the full path shall be
            retrieved.
        :param options: The sharing options such as expiration date in case
            of cloud shares.
        :return: The absolute path to the file from which it can be downloaded
            via http or accessed on the disk.
        """
        _ = filename
        __ = options
        ___ = self
        return None

    def get_statistics(self) -> dict | None:
        """
        Returns statistics about the file source if available.

        Requires a valid file list, see :meth:`get_file_list`.

        :return: Dictionary with statistics about file types, total size etc.
        """
        if self._file_list is None:
            return None
        if self._statistics is not None:
            return self._statistics
        file_type_counter = Counter()
        size_by_filetype = Counter()
        dir_names = set()
        total_size = 0
        for cur_file in self._file_list:
            cur_name = cur_file.filename
            dir_name = os.path.dirname(cur_name)
            extension = os.path.splitext(cur_name)[1]
            dir_names.add(dir_name)
            file_type_counter[extension] += 1
            size_by_filetype[extension] += cur_file.file_size
            total_size += cur_file.file_size
        file_extension_list = sorted(
            list(file_type_counter.keys()),
            reverse=True,
            key=lambda x: file_type_counter[x])
        sorted_keys = sorted(file_type_counter.keys(),
                             reverse=True,
                             key=lambda x: file_type_counter[x])
        ext_details = {
            key: {
                "totalFileSizeMb": size_by_filetype[key] / 1000000.0,
                "totalFileCount": file_type_counter[key]} for key in
            sorted_keys}
        self._statistics = {"totalFileCount": len(self._file_list),
                            "totalFileSizeMb": total_size / 1000000,
                            "totalDirs": len(dir_names),
                            "fileExtensions": file_extension_list,
                            "extensionDetails": ext_details}
        return self._statistics

    def __str__(self):
        result = self.__class__.__name__ + "\n"
        statistics = self.get_statistics()
        from scistag.common.dict_helper import dict_to_bullet_list
        if statistics is not None:
            result += dict_to_bullet_list(statistics)
        result += f"* search-mask: {self.search_mask}"
        return result

    def __iter__(self) -> FileSourceIterator:
        """
        Returns an iterator object for this file source
        :return: The iterator
        """
        return FileSourceIterator(self)

    def __enter__(self) -> "FileSource":
        """
        Provides the FileSource context. Allows automated clean closing of
        a file source via

        ``with FileSource.from_path("./my_folder") as source``

        as once the with with-block is left it will automatically call the
        source's :meth:`close` function.

        :return: The FileSource object
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Closes the context (and in consequence open connections, archives etc.)
        """
        if not self.is_closed:
            self.close()

    def __len__(self) -> int:
        """
        Returns the count of files of the file source (if fetch_file_list is
        True)

        :return: The count of elements
        """
        return len(self._file_list) if self._file_list is not None else 0

    def __contains__(self, item):
        """
        Returns true if the file with given name exists

        :param item: The name of the file
        :return: True if the file exists
        """
        return item in self._file_set

    @abstractmethod
    def _read_file_int(self, filename: str) -> bytes | None:
        """
        Reads a file from this file source, identified by name.

        Note: Not all FileSources support direct file access by name, so you
        should always prefer to just iterate through a FileSource object rather
        than accessing single files if your FileSource can be freely configured.
        For example an :class:`ImageFileSource` pointing to a camera can only
        provide it's data frame by frame - and thus image file by image file -
        and not by name.

        :param filename: The name of the file to read
        :return: The file's content on success, None otherwise
        """
        return None

    def read_file(self, filename: str) -> bytes | None:
        """
        Reads a file from this file source, identified by name.

        Note: Not all FileSources support direct file access by name, so you
        should always prefer to just iterate through a FileSource object rather
        than accessing single files if your FileSource can be freely configured.
        For example an :class:`ImageFileSource` pointing to a camera can only
        provide it's data frame by frame - and thus image file by image file -
        and not by name.

        :param filename: The name of the file to read
        :return: The file's content on success, None otherwise
        """
        from scistag.webstag import WebCache
        if self.max_web_cache_age != 0:  # try to fetch data if cache is on
            unique_name = self._get_source_identifier() + "/" + filename
            try:
                data = WebCache.fetch(unique_name,
                                      max_age=self.max_web_cache_age)
            except:
                data = None
            if data is not None:
                return data
        result = self._read_file_int(filename)
        if self.max_web_cache_age != 0:  # store new data if cache is on
            unique_name = self._get_source_identifier() + "/" + filename
            WebCache.store(unique_name, result)
        return result

    def exists(self, filename: str) -> bool:
        """
        Verifies if a file exists.

        Note: This function may not be supported by all sources (such as
        streaming sources)

        :param filename: The file to look for
        :return: True if the file exists
        """
        if self._file_set is not None:
            return filename in self._file_set
        raise NotImplementedError("Missing implementation for exists method")

    def update_file_list(self, new_list: list[FileListEntry], may_sort=True):
        """
        Call this function if you want to manually update the file list.

        Updates the internal search index and other helper variables.

        :param new_list: The new list
        :param may_sort: Defines if the list may be sorted
        """
        self._file_list = new_list
        if self.sorting_callback is not None and may_sort:  # apply sorting
            self._file_list = sorted(self._file_list, key=self.sorting_callback)
        self._file_set = set([element.filename for element in new_list])
        self._statistics = None

    def reduce_file_list(self) -> list[FileListEntry] | None:
        """
        Reduces the :attr:`file_list` by applying all filters (index_range,
        max_file_count, filter_callback) in  advance. Requires the source being
        initialized with fetch_file_list in advance and thus requires a
        non-streaming file source where the full file list is known in advance.

        This way you know in advance which files (after all the filters) are
        really getting processed with your current filtering settings. So the
        filters are not applied twice this function also disables all
        callbacks and filter variables after it's execution.

        :return: Returns the reduced file list
        """
        if self._file_list is None:
            return None
        output_filenames = []
        cleaned_list = []
        for index, element in enumerate(self._file_list):
            file_info = FileIterationData(self, index,
                                          element=element)
            new_filename = self.handle_skip_check(file_info)
            if new_filename is None:
                continue
            cleaned_list.append(element)
            output_filenames.append(new_filename)
        if self.max_file_count != -1 and len(
                cleaned_list) > self.max_file_count:
            cleaned_list = cleaned_list[0:self.max_file_count]
            output_filenames = output_filenames[0:self.max_file_count]
        self.output_filename_list = output_filenames
        self.update_file_list(cleaned_list)
        self.max_file_count = -1
        self.index_filter = None
        self.filter_callback = None
        return self._file_list

    def handle_next(self,
                    iterator: FileSourceIterator) -> FileSourceElement | None:
        """
        Returns the next available element

        :param iterator: The iterator object which keeps track of the current
            processing
        :return: The next file object if available
        """
        if (self.max_file_count != -1 and
                iterator.processed_file_count >= self.max_file_count):
            raise StopIteration
        while True:
            next_entry = self.handle_get_next_entry(iterator)
            if next_entry is None:  # stop if no files are available anymore
                return None
            # was already filtered using reduce_file_list
            if self.output_filename_list is not None:
                target_name = self.output_filename_list[iterator.file_index - 1]
            else:
                target_name = self.handle_skip_check(
                    FileIterationData(self, iterator.file_index - 1,
                                      element=next_entry))
            # continue if just the current file is skipped
            if target_name is not None:
                break
        data = self.read_file(
            next_entry.filename) if not self.dont_load else None
        return self.handle_provide_result(iterator, target_name, data)

    def handle_get_next_entry(self, iterator: "FileSourceIterator") -> \
            FileListEntry | None:
        """
        Returns the FileListEntry containing all information about the next file
        to be processed.

        Overwrite this method for your own, custom File iterator.

        :param iterator: The file iterator object
        :return: All details about the next file to be processed. None if no
            file needs to be processed anymore.
        """
        index = iterator.file_index
        iterator.file_index += 1
        if self._file_list is None:
            return None
        if index >= len(self._file_list):
            return None
        return self._file_list[index]

    def handle_fetch_file_list(self, force: bool = False) -> None:
        """
        Called when the file list shall be pre-fetched.

        If your custom FileSource is able to do so populate the self.file_list
        with a sorted list of all files available and instead of iterating the
        files live always access the matching file list entry using
        self.file_list[file_index] appropriately.

        :param force: Enforce an update of the file list, even if it was created
            before already
        """
        pass

    def _create_file_list_int(self, no_cache: bool = False):
        """
        Creates the file list by either scanning the source directory or
        loading a cache file list from disk.

        If caching is enabled the new list is stored to disk.

        :param no_cache: If defined the file list may not be loaded form disk,
            e.g. when this function is called from :meth:`refresh`.
        """
        loaded = False
        if self._file_list_name is not None and not no_cache:
            loaded = self.load_file_list(self._file_list_name,
                                         version=self._file_list_version)
        if not loaded:
            self.handle_fetch_file_list()
        if not loaded and self._file_list_name is not None:
            self.save_file_list(self._file_list_name,
                                version=self._file_list_version)

    def handle_file_list_filter(self, entry: FileListEntry) -> bool:
        """
        Verifies if the file is valid and shall be processed by comparing it to
        the file mask, the index_filter etc.

        Increases the file_index upon failure. Does NOT increase it upon success
        (as :meth:`provide_result` will do so).

        :param entry: The file entry to verify
        :return: A valid filename if the file shall be processed,
            None otherwise.
        """
        if not fnmatch(os.path.basename(entry.filename), self.search_mask):
            return False
        rest = entry.filename[len(self.search_path):].lstrip("/").lstrip("\\")
        if not self.recursive:
            if "/" in rest or "\\" in rest:
                return False
        return True

    def handle_skip_check(self, file_info: FileIterationData) -> str | None:
        """
        Verifies if the file is valid and shall be processed by comparing it to
        the file mask, the index_filter etc.

        Increases the file_index upon failure. Does NOT increase it upon success
        (as :meth:`provide_result` will do so).

        :param file_info: Information about the current file
        :return: A valid filename if the file shall be processed, None otherwise.
        """
        filename = file_info.element.filename
        if self.index_filter is not None:
            if (file_info.file_index % self.index_filter[0] !=
                    self.index_filter[1]):
                return None
        if self.filter_callback is not None:
            result = self.filter_callback(file_info)
            if result is None:
                return None
            if isinstance(result, bool):
                if not result:
                    return None
            else:
                filename = result
        return filename

    # noinspection PyMethodMayBeStatic
    def handle_provide_result(self, iterator: FileSourceIterator, filename: str,
                              data: bytes) -> FileSourceElement:
        """
        Provides the file result for the current iterator index

        :param iterator: The iterator handle
        :param filename: The name of the file to be stored
        :param data: The file data
        """
        iterator.processed_file_count += 1
        return FileSourceElement(data=data, name=filename)

    def close(self):
        """
        Closes the current file source, e.g. zip archive, streaming connection
        etc. if applicable
        """
        self.is_closed = True
