"""
Defines a set of supported file stag protocols for storing and received file
data from different sources.
"""
from __future__ import annotations

AZURE_PROTOCOL_HEADER = "azure://"
"SciStag identifier for Azure storage"

AZURE_DEFAULT_ENDPOINTS_HEADER = "DefaultEndpoints"
"The header with which an Azure connection string begins"

ZIP_SOURCE_PROTOCOL = "zip://"
"A file path flagging the file as being stored in a zipfile"
