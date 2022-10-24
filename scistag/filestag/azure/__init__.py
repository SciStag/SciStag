"""
Module integrating the Azure specific extensions for FileStag
"""

from .azure_storage_file_source import AzureStorageFileSource
from .azure_storage_file_sink import AzureStorageFileSink

__all__ = ["AzureStorageFileSource", "AzureStorageFileSink"]
