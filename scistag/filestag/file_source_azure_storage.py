"""
Implements the :class:`FileSourceAzureStorage` class which allows iterating
files stored in an Azure Blob Storage
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from collections.abc import Iterable
from scistag.filestag.file_source import FileSource, FileSourceIterator, \
    FileListEntry

if TYPE_CHECKING:
    from azure.storage.blob import BlobServiceClient, ContainerClient

AZURE_PROTOCOL_HEADER = "azure://"
"SciStag identifier for Azure storage"
DEFAULT_ENDPOINTS_HEADER = "DefaultEndpoints"
"The header with which an Azure connection string begins"


class FileSourceAzureStorage(FileSource):
    """
    FileSource implementation for processing files store in an Azure storage
    blob

    All you have to do is to provide a blob storage's connection string and
    container name, optionally further search parameters such as the file and
    then run

    ``for cur_file in FileSourceAzure("azure://DefaultEnd=...=...;AccountKey=...
    /container/path:", mask="*.png"): ...``

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
        if not source.startswith(AZURE_PROTOCOL_HEADER):
            raise ValueError(
                "source has be in the form azure://DefaultEndpoints...")
        source, container, search_path = self.split_azure_url(source)
        assert len(container)
        self.service_client: "BlobServiceClient" = \
            self.service_from_connection_string(source)
        "Connector to the Azure storage"
        self.container_client: "ContainerClient" = \
            self.service_client.get_container_client(container)
        "Connector to a specific container"
        self.connection_string = source
        "The connection string"
        self.container_name = container
        "The container's name"
        self.prefix = search_path + "/" if len(search_path) else ""
        "The prefix (base folder) if specified"
        self.tag_filter_expression = tag_filter if tag_filter is not None and \
                                                   len(tag_filter) > 0 else None
        """
        A tag filter. If specified all files containing specific tags will be
         selected
        """
        self.results_per_page = 100
        "The maximum count of file names to fetch in one batch"
        if self.max_file_count != -1:
            self.results_per_page = self.max_file_count
        if params.get("fetch_file_list", False):
            loaded = False
            if self._file_list_name is not None:
                loaded = self.load_file_list(self._file_list_name,
                                             version=self._file_list_version)
            if not loaded:
                self.handle_fetch_file_list()
            if self._file_list_name is not None:
                self.save_file_list(self._file_list_name,
                                    version=self._file_list_version)

    @staticmethod
    def service_from_connection_string(
            connection_string: str) -> "BlobServiceClient":
        """
        Creates a blob service connection using the provided connection string
        :param connection_string: Connection string of the from
            DefaultEndpoints...
        :return: The blob client
        """
        from azure.storage.blob import BlobServiceClient
        return BlobServiceClient.from_connection_string(connection_string)

    def _get_source_identifier(self) -> str:
        return f"{self.connection_string}|{self.container_name}"

    @classmethod
    def split_azure_url(cls, url: str) -> tuple[str, str, str] | None:
        """
        Splits an Azure url of the foamt ``azure://CONNECTION_STRING_INCLUDING_KEY/container_name`` into its
        components.

        :param url: The URL
        :return: ConnectionString, ContainerName, SearchPath. If the container
            name or the search path are not provided, empty strings will be
            returned.
        """
        if not url.startswith(AZURE_PROTOCOL_HEADER):
            return None
        url = url[len(AZURE_PROTOCOL_HEADER):]
        container_name_token = "core.windows.net/"
        if container_name_token in url:
            index = url.index(container_name_token) + len(
                container_name_token) - 1
            connection_string, container = url[0:index], url[index + 1:]
            search_path = ""
            if "/" in container:
                index = container.index("/")
                container, search_path = container[0:index], container[
                                                             index + 1:]
                search_path = search_path.rstrip("/")
            return connection_string, container, search_path
        return url, "", ""

    def _read_file_int(self, filename: str) -> bytes | None:
        from azure.core.exceptions import ResourceNotFoundError
        try:
            return self.container_client.download_blob(filename).readall()
        except ResourceNotFoundError:
            return None

    def exists(self, filename: str) -> bool:
        if self._file_list is not None:
            return super().exists(filename)
        blob_client = self.container_client.get_blob_client(filename)
        return blob_client.exists()

    def handle_get_next_filename(self, iterator: FileSourceIterator) -> \
            tuple[str, int] | None:
        while True:
            if iterator.file_index == 0:
                iterator.processing_data[
                    'blobIter'] = self.setup_blob_iterator()
            iterator.file_index += 1
            try:
                next_element = next(iterator.processing_data['blobIter'])
                if self.tag_filter_expression is not None:
                    filename: str = next_element["name"]
                    file_size: int = 0
                else:
                    filename: str = next_element.name
                    file_size: int = next_element.size
            except StopIteration:
                iterator.processing_data['blobIter'] = None
                return None
            if not self.handle_file_list_filter(filename):
                continue
            return filename, file_size

    def setup_blob_iterator(self) -> Iterable:
        """
        Setups the blob iterator

        :return: The iterator object, e.g. returned by list_blobs or
            find_blobs_by_tag.
        """
        if self.tag_filter_expression is None:
            return iter(
                self.container_client.list_blobs(
                    name_starts_with=self.prefix,
                    results_per_page=self.results_per_page,
                    timeout=self.timeout))
        # filter by tag
        return self.container_client.find_blobs_by_tags(
            filter_expression=self.tag_filter_expression,
            results_per_page=self.results_per_page,
            timeout=self.timeout)

    def handle_file_list_filter(self, filename: str) -> bool:
        if self.tag_filter_expression is not None and len(self.prefix):
            if not filename.startswith(self.prefix):
                return False
        return super().handle_file_list_filter(filename)

    def handle_fetch_file_list(self, force: bool = False):
        if self._file_list is not None and not force:
            return
        from scistag.common.iter import limit_iter
        blob_iterator = self.setup_blob_iterator()
        if self.tag_filter_expression is not None:
            cleaned_list = [(element['name'], 0)
                            for element in
                            limit_iter(blob_iterator, self.max_file_count)
                            if self.handle_file_list_filter(element['name'])]
        else:
            cleaned_list = [(element.name, element.size)
                            for element in
                            limit_iter(blob_iterator, self.max_file_count) if
                            self.handle_file_list_filter(element.name)]
        elements = sorted(cleaned_list, key=lambda element: element[0])
        self.update_file_list(
            [FileListEntry(filename=element[0], file_size=element[1]) for
             element in elements])

    def close(self):
        if self.is_closed:
            return
        self.service_client = None
        self.container_client = None
        super().close()
