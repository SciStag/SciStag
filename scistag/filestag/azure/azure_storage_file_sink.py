"""
Implements the class :class:`FileSinkAzureStorage` which helps storing files
in an Azure Storage.
"""

from __future__ import annotations

from typing import Union, TYPE_CHECKING

from scistag.filestag import FileSink, FileStorageOptions
from scistag.filestag.azure.azure_storage_file_source import \
    AzureStorageFileSource
from scistag.filestag.protocols import AZURE_PROTOCOL_HEADER, \
    AZURE_DEFAULT_ENDPOINTS_HEADER

if TYPE_CHECKING:
    from azure.storage.blob import BlobServiceClient, ContainerClient


class AzureStorageFileSink(FileSink):
    """
    Helper class for storing files in Azure storage
    """

    def __init__(self,
                 target: str | None = None,
                 service: "BlobServiceClient" | str | None = None,
                 container: "ContainerClient" | str | None = None,
                 create_container=True,
                 recreate_container: bool = False,
                 sub_folder: str | None = None,
                 **params):
        """
        :param target: A FileStag conform Azure Storage URL of the form
            azure://DefaultEndspoints...key=.../ContainerNam/SubFolder/Logs/
            azure://DefaultEndspoints...key=.../ContainerName or
            azure://DefaultEndspoints...key=... w/o. container name if you
            provided it separately as string.
        :param service: The blob service to use or a connection string of the
            form DefaultEndpoints...
        :param container: The container in which the file shall be stored
        :param create_container: Defines if the container may be created if it
            does not exist yet.

            True by default.
        :param recreate_container: Defines if we shall delete the old container
            and all it's contents to create a "fresh"
        :param sub_folder: If provided all uploaded files will be stored in
            this "virtual" sub folder instead of the container's root,
            e.g. "images/".
        :param params: Additional initializer parameters. See :class:`FileSink`.
        """
        super().__init__(target=target, **params)
        if sub_folder is None:
            sub_folder = ""
        if target is not None:
            if not target.startswith(AZURE_PROTOCOL_HEADER):
                raise ValueError(
                    "Target has to be in the form azure://DefaultEndPoints...")
            conn_str, _container, mask = AzureStorageFileSource.split_azure_url(
                target)
            if len(_container):
                container = _container
            if mask:
                sub_folder = mask
            service = conn_str
        if len(sub_folder) > 0 and not sub_folder.endswith("/"):
            sub_folder += "/"
        if service is not None and isinstance(service, str):
            from azure.storage.blob import BlobServiceClient
            # setup from connection string if provided
            if service.startswith(AZURE_DEFAULT_ENDPOINTS_HEADER):
                service = BlobServiceClient.from_connection_string(service)
            else:
                raise ValueError("Connection string has the wrong format")
        if service is None:
            raise ValueError("No service client or url provided")
        if container is None:
            raise ValueError("No container client or url provided")
        if isinstance(container, str):
            container = \
                self.setup_container(service=service,
                                     container_name=container,
                                     create=create_container,
                                     recreate_container=recreate_container)
            if container is None:
                raise ValueError("Could not access container")
        self.service = service
        self.container = container

    def _store_int(self,
                   filename: str,
                   data: bytes,
                   overwrite: bool,
                   options: FileStorageOptions | None = None) -> bool:
        return self.upload_file(filename=filename,
                                data=data,
                                container=self.container,
                                overwrite=overwrite)

    @classmethod
    def upload_file(cls,
                    filename: str,
                    data: bytes,
                    service: Union["BlobServiceClient", str, None] = None,
                    container: Union["ContainerClient", str, None] = None,
                    overwrite=True,
                    create_container=True) -> bool:
        """
        Uploads a file into the Azure storage

        :param filename: The name of the file
        :param data: The data to be uploaded
        :param service: The blob service to use or a connection string of the
            form DefaultEndpoints...
        :param container: The container in which the file shall be stored
        :param overwrite: Defines if the file may be overwritten.

            True by default.
        :param create_container: Defines if the container may be created if it
            does not exist yet.

            True by default.
        :return: Defines if the file could be uploaded successfully.
        """
        if filename.startswith(AZURE_PROTOCOL_HEADER):
            con_str, container, search_path = \
                AzureStorageFileSource.split_azure_url(filename)
            if len(container) == 0:
                raise ValueError("No container name provided")
            if len(search_path) == 0:
                raise ValueError("No filename provided")
            service = AzureStorageFileSource.service_from_connection_string(
                con_str)
            container = cls.setup_container(service, container_name=container,
                                            create=create_container)
            filename = search_path
        if data is None:
            raise ValueError("No data provided")
        if service is not None and isinstance(service, str):
            # setup from connection string if provided
            from azure.storage.blob import BlobServiceClient
            if service.startswith(AZURE_DEFAULT_ENDPOINTS_HEADER):
                service = BlobServiceClient.from_connection_string(service)
        if service is None:
            from azure.storage.blob import ContainerClient
            if container is None or not isinstance(container, ContainerClient):
                raise ValueError(
                    "No service client, valid container nor url provided")
        if container is None:
            raise ValueError("No container client or url provided")
        if isinstance(container, str):
            container = cls.setup_container(service,
                                            container_name=container,
                                            create=create_container)
            if container is None:
                raise ValueError("Could not access container")
        from azure.core.exceptions import ClientAuthenticationError, \
            ResourceExistsError
        try:
            blob_client = container.get_blob_client(filename)
            blob_client.upload_blob(data, overwrite=overwrite)
        except (ClientAuthenticationError, ResourceExistsError):
            return False
        return True

    @staticmethod
    def setup_container(service: "BlobServiceClient",
                        container_name: str,
                        create: bool = True,
                        reuse_existing: bool = True,
                        recreate_container: bool = False) -> \
            Union["ContainerClient", None]:
        """
        Setups a container to prepare it for storing files in it

        :param service: The service client via which we are connected
            to the Azure storage
        :param container_name: The name of the container we want to access
        :param create: Defines if we can create a new container if it
            does not exist yet
        :param reuse_existing: If this is set to true and the container we
            want to create already exists, it will not try to open the
            existing one but will return None instead. This way cou can
            react, by for example trying an alternative name such as
            results_0000, results_0001 etc.
        :param recreate_container: Defines if we shall delete the old container
            and all it's contents to create a "fresh"
        :return: The container client if we could access or create the
            container successfully, otherwise None.
        """
        from azure.core.exceptions import ResourceExistsError, \
            ResourceNotFoundError
        container_client = None
        try:
            if not create:
                try:
                    return service.get_container_client(
                        container_name)
                except ResourceNotFoundError:
                    return None
            container_client = service.create_container(container_name)
        except ResourceExistsError:
            if not recreate_container:
                if not reuse_existing:
                    return None
                container_client = service.get_container_client(
                    container_name)
            else:
                service.delete_container(container_name)
                import time
                start_time = time.time()
                delete_timeout = 60.0
                sleep_time = 0.25
                while time.time() - start_time < delete_timeout:
                    try:
                        container_client = service.create_container(
                            container_name)
                        break
                    except ResourceExistsError as E:
                        time.sleep(sleep_time)
        return container_client
