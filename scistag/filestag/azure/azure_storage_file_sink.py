"""
Implements the class :class:`AzureStorageFileSink` which helps storing files
in an Azure Storage.
"""

from __future__ import annotations

from typing import Union, TYPE_CHECKING

import scistag.tests
from scistag.filestag import FileSink, FileStorageOptions
from scistag.filestag.azure.azure_blob_path import AzureBlobPath
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
                 delete_timeout_s=60.0,
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
        :param delete_timeout_s: The timeout in seconds to wait until a
            container can be created again after it has been deleted.
        :param params: Additional initializer parameters. See :class:`FileSink`.
        """
        super().__init__(target=target, **params)
        self.blob_path: AzureBlobPath | None
        if sub_folder is None:
            sub_folder = ""
        if target is not None:
            if not target.startswith(AZURE_PROTOCOL_HEADER) and not \
                    target.startswith(AZURE_DEFAULT_ENDPOINTS_HEADER):
                raise ValueError(
                    "Target has to be in the form azure://DefaultEndPoints...")
            self.blob_path = AzureBlobPath.from_string(target)
            if len(self.blob_path.container_name) > 0:
                container = self.blob_path.container_name
            if len(self.blob_path.blob_name) > 0:
                sub_folder = self.blob_path.blob_name
            service = self.blob_path.get_connection_string()
        if len(sub_folder) > 0 and not sub_folder.endswith("/"):
            sub_folder += "/"
        if service is not None and isinstance(service, str):
            from azure.storage.blob import BlobServiceClient
            # setup from connection string if provided
            if service.startswith(AZURE_DEFAULT_ENDPOINTS_HEADER) or \
                    service.startswith(AZURE_PROTOCOL_HEADER):
                connection_string = AzureBlobPath.from_string(
                    service).get_connection_string()
                service = BlobServiceClient.from_connection_string(
                    connection_string)
            else:
                raise ValueError("Connection string has the wrong format")
        if service is None:
            raise ValueError("No service client or url provided")
        if container is None or not isinstance(container, str) or len(
                container) == 0:
            raise ValueError("No container client or url provided")
        if isinstance(container, str):
            container = \
                self.setup_container(service=service,
                                     container_name=container,
                                     create=create_container,
                                     recreate_container=recreate_container,
                                     delete_timeout_s=delete_timeout_s)
            if container is None:
                raise ValueError("Could not access container")
        self.service = service
        "The Azure service client (providing access to containers)"
        self.container = container
        "The Azure container client (providing access to one container)"
        self.sub_folder = sub_folder
        "The folder in which all files uploaded shall be stored"

    def _store_int(self,
                   filename: str,
                   data: bytes,
                   overwrite: bool,
                   options: FileStorageOptions | None = None) -> bool:
        return self.upload_file(filename=self.sub_folder + filename,
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
        if filename.startswith(AZURE_PROTOCOL_HEADER) or filename.startswith(
                "DefaultEndpoints"):
            blob_path = AzureBlobPath.from_string(filename)
            if len(blob_path.container_name) == 0:
                raise ValueError("No container name provided")
            if len(blob_path.blob_name) == 0:
                raise ValueError("No filename provided")
            service = AzureStorageFileSource.service_from_connection_string(
                blob_path.get_connection_string())
            container = \
                cls.setup_container(service,
                                    container_name=blob_path.container_name,
                                    create=create_container)
            filename = blob_path.blob_name
        if data is None:
            raise ValueError("No data provided")
        if service is not None and isinstance(service, str):
            # setup from connection string if provided
            from azure.storage.blob import BlobServiceClient
            if service.startswith(AZURE_DEFAULT_ENDPOINTS_HEADER) or \
                    service.startswith(AZURE_PROTOCOL_HEADER):
                blob_path = AzureBlobPath.from_string(service)
                if container is None or not isinstance(container, str):
                    raise ValueError("Container needs to be a string if the "
                                     "service is defined explicitly")
                service = BlobServiceClient.from_connection_string(
                    blob_path.get_connection_string())
                container = cls.setup_container(service,
                                                container_name=container,
                                                create=create_container)
                if container is None:
                    raise ValueError("Container not found")
            else:
                raise ValueError("Invalid connection string")
        if service is None:
            from azure.storage.blob import ContainerClient
            if container is None or not isinstance(container, ContainerClient):
                raise ValueError(
                    "No service client, valid container nor url provided")
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
                        delete_timeout_s: float = 60.0,
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
        :param delete_timeout_s: The timeout in seconds to wait until a
            container can be created again after it has been deleted.
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
                container_client = service.get_container_client(
                    container_name)
                if not container_client.exists():
                    return None
                return container_client
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
                sleep_time = 0.25
                while time.time() - start_time < delete_timeout_s:
                    try:
                        container_client = service.create_container(
                            container_name)
                        break
                    except ResourceExistsError as E:
                        time.sleep(sleep_time)
        return container_client

    def create_sas_url(self, blob_name, start_time_min=-15,
                       end_time_days: float = 365.0) -> str:
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
        return \
            self.blob_path.create_sas_url(self.sub_folder + blob_name,
                                          start_time_min,
                                          end_time_days)
