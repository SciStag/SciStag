"""
Defines a set of supported file stag protocols for storing and received file
data from different sources.
"""
from __future__ import annotations

AZURE_PROTOCOL_HEADER = "azure://"
"SciStag identifier for Azure storage"

AZURE_DEFAULT_ENDPOINTS_HEADER = "DefaultEndpoints"
"The header with which an Azure connection string begins"

AZURE_SAS_URL_COMPONENT = "blob.core.windows.net"
"The path of an Azure SAS URL"


def is_azure_storage_source(source: str):
    """
    Defines if the URL is an Azure storage source

    :param source: The source string, e.g. DefaultEndpoints or an SAS URL
    :return: True if it is an Azure storage source
    """
    return (source.startswith(AZURE_PROTOCOL_HEADER) or
            source.startswith(AZURE_DEFAULT_ENDPOINTS_HEADER) or
            (source.startswith("http") and AZURE_SAS_URL_COMPONENT in source))


ZIP_SOURCE_PROTOCOL = "zip://"
"A file path flagging the file as being stored in a zipfile"
