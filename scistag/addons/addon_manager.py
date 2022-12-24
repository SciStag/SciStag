import copy
import json
import os.path
import hashlib
from fnmatch import fnmatch
from threading import RLock
from typing import Optional, Dict

import scistag.filestag.protocols
import scistag.filestag.shared_archive

FEATURE_FS_PATH = "fspath"

ADDON_DATA_FILENAME = os.path.normpath(
    os.path.dirname(__file__) + "/../data/addon_packages.json"
)
ADDON_DATA_PATH = os.path.dirname(ADDON_DATA_FILENAME)

GROUP_INFO = "info"
GROUP_IGNORE_SET = {"info"}

"Feature name constants"
FEATURE_SIZE = "size"
FEATURE_MD5 = "md5"
FEATURE_INFO = "info"
FEATURE_REMOTE_FILENAMES = "remoteFilenames"
FEATURE_LOCAL_FILENAME = "localFilename"
FEATURE_TEST = "test"

# FileStag access constants
FS_IDENTIFIER_HEADING = "addons."
"""
The shared identifier heading with which all shared zip archives in
FileStag start with
"""
ADDON_FS_BASE_PATH = (
    scistag.filestag.protocols.ZIP_SOURCE_PROTOCOL + f"@{FS_IDENTIFIER_HEADING}"
)
"""
The path under which the addon's data can be accessed using FileStag.load_file 
and FileStag.exists
"""

MAX_S_PER_MB = 4
"Maximum count of seconds we grant to download a single megabyte. 2 MBit."


class AddonManager:
    """
    Manages the optional SciStag addons and their installation from the web.
    """

    access_lock = RLock()
    "Data access lock"
    addon_data: Optional[Dict] = None
    "The addon main dictionary"
    all_addons: Dict = {}
    "A sorted dictionary of all addons"

    @classmethod
    def get_addon_data(cls) -> Optional[Dict]:
        """
        Returns the addon dictionary

        :return: The dictionary. See data/addon_packages.json for details.
        """
        with cls.access_lock:
            if cls.addon_data is not None:
                return cls.addon_data
            cls.addon_data = json.load(open(ADDON_DATA_FILENAME, "r"))
            cls.build_helper_data()
            return cls.addon_data

    @classmethod
    def get_groups(cls) -> Dict:
        """
        Returns a dictionary containing all groups (and their elements)
        :return: The addon dictionary cleared from (future) features.

        A single element has the structure:
        ```javascript
            "groupName": {
                "elements"
            }
        ```
        """
        cls.get_addon_data()  # ensure data is available
        filtered_dict = copy.deepcopy(cls.addon_data)
        return filtered_dict

    @classmethod
    def get_all_addons(cls):
        """
        Returns a list of all addon packages and their respective unique
        identifier. This identifier can then be used by install_addon and
        remove_addon to install or remove a feature.

        :return: A dictionary containing all installable addons
        """
        cls.get_addon_data()  # ensure data is available
        return cls.all_addons

    @classmethod
    def get_installed_addons(cls):
        """
        Returns a list of all installed addon packages and their respective
        unique identifier. This identifier can then be used by install_addon
        and remove_addon to install or remove a feature.

        :return: A dictionary containing all installable addons
        """
        result = {}
        with cls.access_lock:
            for key, element in cls.get_all_addons().items():
                if cls.get_addon_installed(key):
                    result[key] = element
        return result

    @classmethod
    def build_helper_data(cls) -> None:
        """
        Fills helper variables such as the all_addons list for easier
        enumeration
        """
        cls.all_addons = {}
        for g_key, group in cls.get_groups().items():
            group: Dict
            for f_key, feature in group.items():
                if f_key in GROUP_IGNORE_SET:
                    continue
                cls.all_addons[g_key + "." + f_key] = feature

    @classmethod
    def get_addon_installed(cls, feature_name) -> bool:
        """
        Returns if an addon with given name is installed

        :param feature_name: The addon's name, see get_all_addons()
        :return: True if the addon exists.
        """
        with cls.access_lock:
            if feature_name not in cls.get_all_addons():
                return False
            feature = cls.all_addons[feature_name]
            local_path = ADDON_DATA_PATH + "/" + feature[FEATURE_LOCAL_FILENAME]
            return os.path.exists(local_path)

    @classmethod
    def get_local_path(cls, feature_name):
        """
        Returns the local path of a feature

        :param feature_name: The feature's name
        :return: The feature's path. Empty string if invalid
        """
        if feature_name not in cls.all_addons:
            return ""
        feature = cls.all_addons[feature_name]
        return ADDON_DATA_PATH + "/" + feature[FEATURE_LOCAL_FILENAME]

    @classmethod
    def get_addon_healthy(cls, feature_name) -> (bool, str):
        """
        Returns if an addon with given name is installed and it's data file
        healthy

        :param feature_name: The addon's name, see get_all_addons()
        :return: (Health status (bool), Error_text)
        """
        with cls.access_lock:
            if feature_name not in cls.all_addons:
                return False
            feature = cls.all_addons[feature_name]
            local_path = cls.get_local_path(feature_name)
            if not os.path.exists(local_path):
                return False, f'Could not find file "{local_path}"'
            filesize = os.path.getsize(local_path)
            if filesize != feature[FEATURE_SIZE]:
                return (
                    False,
                    f'File size mismatch/ "{local_path}" '
                    f'should have the size {feature[FEATURE_SIZE]}"'
                    f" but has the size {filesize}",
                )
            with open(local_path, "rb") as file_handle:
                md5_hash = hashlib.md5(file_handle.read()).hexdigest()
            if md5_hash != feature[FEATURE_MD5]:
                return (
                    False,
                    f'MD% checksum mismatch/ "{local_path}" '
                    f'should have the MD5 checksum {feature[FEATURE_MD5]}"'
                    f" but has the checksum {md5_hash}",
                )
            return True, "Success"

    @classmethod
    def install_addon(cls, feature_name, verbose_if_installed=True) -> bool:
        """
        Installs given feature

        :param feature_name: The feature's key. As defined in
        :param verbose_if_installed: Defines if no message shall be printed if
            the addon is already installed
        :return:
        """
        with cls.access_lock:
            if cls.get_addon_installed(feature_name):
                if not verbose_if_installed:
                    print(
                        f"\nAddon addon {feature_name} already installed.", flush=True
                    )
                return False
            feature = cls.all_addons[feature_name]
            local_path = cls.get_local_path(feature_name)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            main_url = feature[FEATURE_REMOTE_FILENAMES][0]
            mb_size = feature[FEATURE_SIZE] / (2**20)
            print(
                f"\nInstalling addon {feature_name} from {main_url} "
                f"({mb_size:0.1f} MB)...",
                flush=True,
            )
            from scistag.webstag import web_fetch

            web_fetch(
                url=main_url,
                filename=local_path,
                timeout_s=int(2 + mb_size * MAX_S_PER_MB),
            )
            healthy, error = cls.get_addon_healthy(feature_name)
            if healthy:
                print("Installation successful", flush=True)
            else:
                print(f"Installation failed: {error}", flush=True)
                return False
            return True

    @classmethod
    def remove_addon(cls, feature_name) -> bool:
        """
        Removes given addons, removes all associated files and unregisters in
        the shared archive registry.

        :param feature_name: The feature's key. As defined in
        :return: True if the addon existed and could successfully be removed
        """
        with cls.access_lock:
            if not cls.get_addon_installed(feature_name):
                return False
            local_path = cls.get_local_path(feature_name)
            print(f"Uninstalling addon {feature_name}...", flush=True)
            # if the addon was loaded, unload it
            if FEATURE_FS_PATH in cls.all_addons[feature_name]:
                from scistag.filestag.shared_archive import SharedArchive

                SharedArchive.unload(filename=os.path.normpath(local_path))
            os.remove(local_path)
            if os.path.exists(local_path):
                print(
                    f"Error uninstalling {feature_name}. "
                    f"Data could not be removed.",
                    flush=True,
                )
                return False
            else:
                print(f"Successfully uninstalled {feature_name}.", flush=True)
            return True

    @classmethod
    def get_addons_paths(cls, filter_mask: str) -> Dict:
        """
        Returns the addon paths for FileStag for all addons matching given
        filter_mask, e.g. emoji.*

        :param filter_mask: The addons to search for. Can contains *
            and ? placeholders.
        :return: A dictionary of the filetype str: str for every matched addon
            and it's corresponding FileStag path,
            e.g. `{"emojis.512": "zip://@addons.emojis.512/"}`
        """
        with cls.access_lock:
            addons = cls.get_all_addons()
            valid_addons = set(
                [key for key in addons.keys() if fnmatch(key, filter_mask)]
            )
            result = {}
            for addon_name in valid_addons:
                if not cls.get_addon_installed(addon_name):
                    continue
                addon = cls.all_addons[addon_name]
                fs_path = ADDON_FS_BASE_PATH + addon_name + "/"
                result[addon_name] = fs_path
                if len(addon.get(FEATURE_FS_PATH, "")) > 0:
                    continue
                scistag.filestag.shared_archive.SharedArchive.register(
                    source=cls.get_local_path(addon_name),
                    identifier=FS_IDENTIFIER_HEADING + addon_name,
                )
                addon[FEATURE_FS_PATH] = fs_path
            return result
