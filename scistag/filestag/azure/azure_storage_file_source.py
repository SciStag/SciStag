"""
Implements the :class:`AzureStorageFileSource` class which allows iterating
files stored in an Azure Blob Storage
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Union
from collections.abc import Iterable
from scistag.filestag.azure.azure_blob_path import AzureBlobPath
from scistag.filestag.file_source import (
    FileSource,
    FileListEntry,
    FileSourcePathOptions,
)
from scistag.filestag.file_source_iterator import FileSourceIterator
from scistag.filestag.protocols import is_azure_storage_source

if TYPE_CHECKING:
    from azure.storage.blob import BlobServiceClient, ContainerClient


class AzureStorageFileSource(FileSource):
    """
    FileSource implementation for processing files store in an Azure storage
    blob

    All you have to do is to provide a blob storage's connection string and
    container name, optionally further search parameters such as the file and
    then run

    ..  code-block: python

        for cur_file in AzureStorageFileSource("azure://DefaultEnd=...=...;AccountKey=...
        /container/path:", mask="*.png"): ...

    to automatically connect through the storage and iterate through all files.
    """

    def __init__(self, source: str, tag_filter: str | None = None, **params):
        """
        :param source: The source data definition, awaiting the following format:
            ``azure://CONNECTION_STRING_INCLUDING_KEY/container_name`` or
            ``azure://CONNECTION_STRING_INCLUDING_KEY/container_name/searchPath``
        :param tag_filter: The tag filter to search files by a tag. None by default. See
            https://learn.microsoft.com/en-us/azure/storage/blobs/storage-manage-find-blobs?tabs=azure-portal
            for details.
        :param params: Additional parameters. See :class:`~scistag.filestag.file_source.FileSource` for the full
            parameter list supported by FileSources.
        :keyword int timeout: The timeout in seconds
        """
        self.timeout: int = int(params.pop("timeout", 30))
        "The connection timeout in seconds"
        super().__init__(**params)
        if not is_azure_storage_source(source):
            raise ValueError(
                "source has be an SAS URL, in the form "
                "azure://DefaultEndpoints... or DefaultEndpoints..."
            )

        self.blob_path = AzureBlobPath.from_string(source)
        assert len(self.blob_path.container_name) or self.blob_path.sas_url is not None
        if self.blob_path.is_sas():
            from azure.storage.blob import BlobServiceClient, ContainerClient

            container_client = ContainerClient.from_container_url(
                self.blob_path.get_connection_string()
            )
            service_client = None
        else:
            service_client = self.service_from_connection_string(
                self.blob_path.get_connection_string()
            )
            container_client = service_client.get_container_client(
                self.blob_path.container_name
            )
        self.service_client: Union["BlobServiceClient", None] = service_client
        "Connector to the Azure storage"
        self.container_client: "ContainerClient" = container_client
        "Connector to a specific container"
        self.container_name = self.blob_path.container_name
        "The container's name"
        search_path = self.blob_path.blob_name + self.search_path
        self.search_path = search_path + "/" if len(search_path) else ""
        self.tag_filter_expression = (
            tag_filter if tag_filter is not None and len(tag_filter) > 0 else None
        )
        """
        A tag filter. If specified all files containing specific tags will be
         selected
        """
        self.results_per_page = 100
        "The maximum count of file names to fetch in one batch"
        if self.max_file_count != -1:
            self.results_per_page = self.max_file_count
        if params.get("fetch_file_list", True):
            self._create_file_list_int()

    @staticmethod
    def service_from_connection_string(connection_string: str) -> "BlobServiceClient":
        """
        Creates a blob service connection using the provided connection string
        :param connection_string: Connection string of the from
            DefaultEndpoints...
        :return: The blob client
        """
        from azure.storage.blob import BlobServiceClient

        return BlobServiceClient.from_connection_string(connection_string)

    def _get_source_identifier(self) -> str:
        return f"{self.blob_path}|{self.container_name}"

    def _read_file_int(self, filename: str) -> bytes | None:
        from azure.core.exceptions import ResourceNotFoundError

        entry = FileListEntry(filename=filename)
        if not self.handle_file_list_filter(entry):
            return None
        try:
            return self.container_client.download_blob(
                self.search_path + filename
            ).readall()
        except ResourceNotFoundError:
            return None

    def exists(self, filename: str) -> bool:
        if self._file_list is not None:
            return super().exists(filename)
        entry = FileListEntry(filename=filename)
        if not self.handle_file_list_filter(entry):
            return False
        blob_client = self.container_client.get_blob_client(self.search_path + filename)
        return blob_client.exists()

    @staticmethod
    def _file_list_entry_from_blob(element, spl: int) -> FileListEntry:
        """
        Creates a file list entry from a blob storage entry

        :param element: The blob storage entry
        :param spl: The length of the search mask (prefix)
        :return: The file list entry containing the extracted properties
        """
        return FileListEntry(
            filename=element.name[spl:],
            file_size=element.size,
            modified=element.last_modified,
            created=element.creation_time,
        )

    def handle_get_next_entry(
        self, iterator: FileSourceIterator
    ) -> FileListEntry | None:
        if self._file_list is not None:
            return super().handle_get_next_entry(iterator)
        while True:
            if iterator.file_index == 0:
                iterator.processing_data["blobIter"] = self.setup_blob_iterator()
            iterator.file_index += 1
            try:
                next_element = next(iterator.processing_data["blobIter"])
                if self.tag_filter_expression is not None:
                    if not next_element["name"].startswith(self.search_path):
                        continue
                    new_element = FileListEntry(filename=next_element["name"])
                else:
                    if not next_element.name.startswith(self.search_path):
                        continue
                    new_element = self._file_list_entry_from_blob(
                        next_element, len(self.search_path)
                    )
            except StopIteration:
                iterator.processing_data["blobIter"] = None
                return None
            if not self.handle_file_list_filter(new_element):
                continue
            return new_element

    def setup_blob_iterator(self) -> Iterable:
        """
        Setups the blob iterator

        :return: The iterator object, e.g. returned by list_blobs or
            find_blobs_by_tag.
        """
        if self.tag_filter_expression is None:
            return iter(
                self.container_client.list_blobs(
                    name_starts_with=self.search_path,
                    results_per_page=self.results_per_page,
                    timeout=self.timeout,
                )
            )
        # filter by tag
        return self.container_client.find_blobs_by_tags(
            filter_expression=self.tag_filter_expression,
            results_per_page=self.results_per_page,
            timeout=self.timeout,
        )

    def handle_fetch_file_list(self, force: bool = False):
        if self._file_list is not None and not force:
            return
        from scistag.common.iter_helper import limit_iter

        blob_iterator = self.setup_blob_iterator()
        from azure.core.exceptions import HttpResponseError

        spl = len(self.search_path)
        try:
            if self.tag_filter_expression is not None:
                cleaned_list = [
                    FileListEntry(filename=element.name[spl:])
                    for element in limit_iter(blob_iterator, self.max_file_count)
                    if element["name"].startswith(self.search_path)
                    and self.handle_file_list_filter(
                        FileListEntry(filename=element["name"])
                    )
                ]
            else:
                elements = [
                    self._file_list_entry_from_blob(element, spl)
                    for element in limit_iter(blob_iterator, self.max_file_count)
                ]
                cleaned_list = [
                    element
                    for element in elements
                    if self.handle_file_list_filter(element)
                ]
        except HttpResponseError:
            raise ValueError(
                "Connection error. This is often due to an"
                "outdated connection string or missing "
                "assigned permissions such as LIST."
            )
        elements = sorted(cleaned_list, key=lambda element: element.filename)
        self.update_file_list(elements)

    def close(self):
        if self.is_closed:
            return
        self.service_client = None
        self.container_client = None
        super().close()

    def create_sas_url(
        self, blob_name, start_time_min=-15, end_time_days: float = 365.0
    ) -> str:
        """
        Creates an SAS url pointing to a specific blob so it can be shared
        and downloaded by others.

        :param blob_name: The name of the blob
        :param start_time_min: The start time from when on this URL is
            valid. By default 15 minutes in the past.
        :param end_time_days: The time in days - as floating point value thus
            also half days are valid - until when the link is valid.

            One year by default.
        :return: The https url pointing to the blob which can be shared as
            download link.
        """
        return self.blob_path.create_sas_url(
            self.search_path + blob_name, start_time_min, end_time_days
        )

    def get_absolute(
        self, filename: str, options: FileSourcePathOptions | None = None
    ) -> str | None:
        return self.create_sas_url(filename)
