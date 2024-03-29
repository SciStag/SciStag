"""
Defines the class :class:`AzureBlobPath` which describes a path to a resource
in an Azure blob storage such as the account name, container name, access key
etc.
"""

from __future__ import annotations
from typing import Optional

from pydantic import BaseModel

from scistag.common import Env
from scistag.filestag.protocols import (
    AZURE_PROTOCOL_HEADER,
    AZURE_DEFAULT_ENDPOINTS_HEADER,
    AZURE_SAS_URL_COMPONENT,
)


class AzureBlobPath(BaseModel):
    """
    Defines a path to an Azure Blob Storage resource.

    This path contains at least the account name,
    may contain the access key and path to the blob within the container.
    """

    default_endpoints_protocol: Optional[str] = None
    "The protocol being used such as https"
    account_name: Optional[str] = None
    "The account name"
    endpoint_suffix: Optional[str] = None
    "The endpoint suffix such as core.windows.net"
    account_key: Optional[str] = None
    "The account key, optional"
    container_name: Optional[str] = None
    "The container name, optional"
    blob_name: Optional[str] = None
    "The blob name or search mask, optional"
    sas_url: Optional[str] = None
    "The full SAS url if provided as SAS"

    @classmethod
    def from_string(cls, connection_string: str) -> AzureBlobPath:
        """
        Create an AzureBlobPath object from a provided connection string.

        :param connection_string: The connection string.

            This string can either be in official filetype, starting with
            DefaultEndpoints... or in the FileStag filetype
            azure://DefaultEndpoints... and can optionally contain the container
            name after a slash and either the blob name or search mask after
            an additional slash.

            e.g.
            - DefaultEndpoints..;AccountName=..;AccountKey=...;windows.core.net
            - ...;windows.core.net/container_name
            - ...;windows.core.net/container_name/blob_name
            - ...;windows.core.net/container_name/*.txt
        :return: The AzureBlobPath object
        """
        if (
            connection_string.startswith("http")
            and AZURE_SAS_URL_COMPONENT in connection_string
        ):
            return AzureBlobPath(
                sas_url=connection_string, container_name="", blob_name=""
            )

        source, container, search_path = cls.split_azure_url(
            connection_string, insert_key=True
        )

        source_elements = source.split(";")
        con_props = {}
        for element in source_elements:
            element: str
            if "=" not in element:
                raise ValueError("Missing value in key value pair")
            index = element.index("=")
            con_props[element[0:index]] = element[index + 1 :]
        blob_path = AzureBlobPath(
            default_endpoints_protocol=con_props.get("DefaultEndpoints" "Protocol"),
            account_name=con_props.get("AccountName"),
            endpoint_suffix=con_props.get("EndpointSuffix"),
            account_key=con_props.get("AccountKey", None),
            container_name=container,
            blob_name=search_path,
        )
        if (
            len(blob_path.account_key) != 0
            and blob_path.account_key.startswith("{{")
            and blob_path.account_key.endswith("}}")
        ):
            raise ValueError(
                f"Account key not specified in connection string {connection_string}"
            )
        return blob_path

    @classmethod
    def split_azure_url(
        cls, url: str, insert_key: bool = True
    ) -> tuple[str, str, str] | None:
        """
        Splits an Azure url of the filetype ``azure://CONNECTION_STRING_INCLUDING_KEY/container_name`` into its
        components.

        :param url: The URL
        :param insert_key: If true a referenced key using for example
            {{env.ENVIRONMENT_VARIABLE}} as filetype will automatically be
            inserted. True by default.
        :return: ConnectionString, ContainerName, SearchPath. If the container
            name or the search path are not provided, empty strings will be
            returned.
        """
        if url.startswith("http") and AZURE_SAS_URL_COMPONENT in url:
            return url, "", ""
        if not url.startswith(AZURE_PROTOCOL_HEADER) and not url.startswith(
            AZURE_DEFAULT_ENDPOINTS_HEADER
        ):
            return None
        if not url.startswith(AZURE_DEFAULT_ENDPOINTS_HEADER):
            url = url[len(AZURE_PROTOCOL_HEADER) :]
        if insert_key:
            url = Env.insert_environment_data(url)
        container_name_token = "core.windows.net/"
        if container_name_token in url:
            index = url.index(container_name_token) + len(container_name_token) - 1
            connection_string, container = url[0:index], url[index + 1 :]
            search_path = ""
            if "/" in container:
                index = container.index("/")
                container, search_path = container[0:index], container[index + 1 :]
                search_path = search_path.rstrip("/")
            return connection_string, container, search_path
        return url, "", ""

    def get_connection_string(self) -> str:
        """
        Returns the connection string to create a BlobServiceClient

        :return: The connection credentials
        """
        epp = self.default_endpoints_protocol
        if self.sas_url is not None:
            return self.sas_url
        if self.account_key is not None:
            return (
                f"DefaultEndpointsProtocol={epp};"
                f"AccountName={self.account_name};"
                f"AccountKey={self.account_key};"
                f"EndpointSuffix={self.endpoint_suffix}"
            )
        else:
            return (
                f"DefaultEndpointsProtocol={epp};"
                f"AccountName={self.account_name};"
                f"EndpointSuffix={self.endpoint_suffix}"
            )

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
        if self.sas_url is not None:
            raise ValueError("Can not create SAS w/o connection string as of now")
        import datetime as dt
        from azure.storage.blob import (
            BlobSasPermissions,
            generate_blob_sas,
        )

        days = int(end_time_days)
        rest = end_time_days - days
        minutes = round(rest * 24 * 60)
        sas = generate_blob_sas(
            account_name=self.account_name,
            container_name=self.container_name,
            account_key=self.account_key,
            blob_name=blob_name,
            permission=BlobSasPermissions(read=True),
            start=dt.datetime.utcnow() + dt.timedelta(minutes=start_time_min),
            expiry=dt.datetime.utcnow() + dt.timedelta(days=days, minutes=minutes),
        )
        sas_url = (
            f"{self.default_endpoints_protocol}://"
            f"{self.account_name}.blob."
            f"{self.endpoint_suffix}/"
            f"{self.container_name}/{blob_name}?{sas}"
        )
        return sas_url

    def is_sas(self):
        """
        Defines if this URL uses a SAS url

        :return: True if we are using a SAS instead of a connection string
        """
        return self.sas_url is not None
