"""
The web_fetch module grants easy access to data in the web via it's web_fetch
function, a one-liner to receive a file via http within a given timeout.
"""

from __future__ import annotations

import hashlib
from threading import RLock

import time
import os
import tempfile
import shutil

FROM_CACHE = "fromCache"
"Defines if the file was loaded from the local disk cache"
HEADERS = "headers"
"Defines the dictionary element containing the response's headers"
STATUS_CODE = "statusCode"
"The response http status code, e.g. 200"
STORED_IN_CACHE = "storedInCache"
"Defines if the file was added to the local disk cache"


def file_age_in_seconds(pathname: str) -> float:
    """
    Returns the age of a file in seconds

    :param pathname: The file's path
    :return The age in seconds:
    """
    stat = os.stat(pathname)
    return time.time() - stat.st_mtime


class WebCache:
    """
    The WebCache class allows the temporary storage of downloaded files in
    the temp directory. How long the file is rated as "valid" can be passed via
    (for example) the wbe_fetch function's cache duration parameter.
    """

    lock = RLock()
    "Access lock"
    cache_dir = tempfile.gettempdir() + "/scistag/"
    "The cache directory"
    app_name = "scistag"
    "The application's name"
    max_general_age = 60 * 60 * 7
    "The maximum age of any file loaded via the cache"
    max_cache_size = 200000000
    "The maximum file size in the cache"
    total_size = 0
    "Total cache size"
    files_stored = 0
    "Files stored in this session"
    cleaned = False
    "Defines if the cache was cleaned yet"

    @classmethod
    def set_app_name(cls, name: str):
        """
        Modifies the application's name (and thus the cache path)

        :param name: The application's name
        """
        with cls.lock:
            cls.app_name = name
            cls.cache_dir = tempfile.tempdir + f"/scistag/{name}/"
            os.makedirs(cls.cache_dir, exist_ok=True)
            cls.cleanup()

    @classmethod
    def fetch(cls, url: str, max_age: float) -> bytes | None:
        """
        Tries to fetch a file from the cache

        :param url: The original url
        :param max_age: The maximum age in seconds
        :return: On success the file's content
        """
        encoded_name = cls.encoded_name(url)
        full_name = cls.cache_dir + encoded_name
        try:
            with cls.lock:
                if os.path.exists(full_name):
                    if file_age_in_seconds(full_name) <= max_age:
                        return open(full_name, "rb").read()
                    cls.remove_outdated_file(full_name)
                return None
        except FileNotFoundError:
            return None

    @classmethod
    def remove_outdated_file(cls, full_name):
        """
        Removes an outdated file from the cache

        :param full_name: The file's name
        """
        cls.total_size -= os.stat(full_name).st_size
        os.remove(full_name)

    @staticmethod
    def encoded_name(name: str) -> str:
        """
        Encodes a filename

        :param name: The filename
        :return: The encoded filename
        """
        return hashlib.md5(name.encode("utf-8")).hexdigest()

    @classmethod
    def find(cls, url: str) -> str | None:
        """
        Searches for a file in the cache and returns it's disk path

        :param url: The http url of the file to search for
        :return: The file name if the file could be found
        """
        encoded_name = cls.encoded_name(url)
        full_name = cls.cache_dir + encoded_name
        if os.path.exists(full_name):
            return full_name
        return None

    @classmethod
    def store(cls, url: str, data: bytes):
        """
        Caches the new web element on disk.

        :param url: The url of the file being stored
        :param data: The data of the file being stored as bytes string
        """
        if not cls.cleaned:
            WebCache.cleanup()
        with cls.lock:
            cls.files_stored += 1
            if cls.files_stored == 1:
                os.makedirs(cls.cache_dir, exist_ok=True)
            if cls.total_size >= cls.max_cache_size:
                cls.flush()
            encoded_name = cls.encoded_name(url)
            full_name = cls.cache_dir + encoded_name
            with open(full_name, "wb") as file:
                file.write(data)
            cls.total_size += len(data)

    @classmethod
    def cleanup(cls):
        """
        Cleans up the cache and removes old files
        """
        with cls.lock:
            cls.cleaned = True
            try:
                files = os.listdir(cls.cache_dir)
            except FileNotFoundError:
                files = []
            cur_time = time.time()
            cls.total_size = 0
            for cur_file in files:
                full_name = cls.cache_dir + cur_file
                stat = os.stat(full_name)
                if cur_time - stat.st_mtime > cls.max_general_age:
                    os.remove(full_name)
                else:
                    cls.total_size += stat.st_size
            if cls.total_size >= cls.max_cache_size:
                # still very unelegant way, should delete files sorted by age
                cls.flush()

    @classmethod
    def flush(cls):
        """
        Clean the cache completely
        """
        with cls.lock:
            cls.total_size = 0
            try:
                shutil.rmtree(cls.cache_dir)
            except FileNotFoundError:
                pass
            os.makedirs(cls.cache_dir, exist_ok=True)


def web_fetch(
    url: str,
    timeout_s: float = 10.0,
    max_cache_age=0.0,
    cache: bool | None = None,
    filename: str | None = None,
    out_response_details: dict | None = None,
    all_codes=False,
    **_,
) -> bytes | None:
    """
    Fetches a file from the web via HTTP GET

    :param url: The URL
    :param timeout_s: The timeout in seconds
    :param max_cache_age: The maximum cache age in seconds. Note that the
        internal cache is everything else than optimized so this should only be
        used to load e.g. the base data for an app once.
    :param cache: If set the default max cache age will be used
    :param filename: If specified the data will be stored in this file
    :param out_response_details: Dictionary target to retrieve response details
        such as
        * headers - The response headers
        * statusCode - The request's http status code
        * fromCache - Defines if the files was loaded from cache
        * storedInCache - Defines if the file was added to the cache
    :param all_codes: Defines if all http return codes shall be accepted.
        Pass a dictionary to response_details for the details.
    :return: The file's content if available and not timed out, otherwise None
    """
    from_cache = False
    if cache is not None and cache:
        max_cache_age = 24 * 60 * 60 * 7
    if max_cache_age != 0:
        data = WebCache.fetch(url, max_age=max_cache_age)
        if data is not None:
            if out_response_details is not None:
                out_response_details[FROM_CACHE] = True
            if filename is not None:
                with open(filename, "wb") as file:
                    file.write(data)
            return data
        else:
            if out_response_details is not None:
                out_response_details[FROM_CACHE] = False
    import requests

    try:
        response = requests.get(url=url, timeout=timeout_s)
    except requests.exceptions.RequestException:
        return None
    if all_codes or response.status_code != 200:
        return None
    if max_cache_age != 0 and response.status_code == 200 and not from_cache:
        WebCache.store(url, response.content)
        if out_response_details is not None:
            out_response_details[STORED_IN_CACHE] = True
    if filename is not None:
        with open(filename, "wb") as file:
            file.write(response.content)
    if out_response_details is not None:
        out_response_details[STATUS_CODE] = response.status_code
        out_response_details[HEADERS] = response.headers
    return response.content


__all__ = [
    "web_fetch",
    "WebCache",
    "FROM_CACHE",
    "STATUS_CODE",
    "HEADERS",
    "STORED_IN_CACHE",
]
"Exported symbols"
