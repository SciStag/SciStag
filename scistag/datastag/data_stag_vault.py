from __future__ import annotations
import time
import fnmatch
from collections import defaultdict
from threading import RLock
from .data_stag_common import StagDataTypes, StagDataReturnTypes
from .data_stag_element import DataStagElement
from .data_stag_list import DataStagList


class DataStagVault:
    """
    The root access point to a DataStag
    """

    FOLDER_SEPARATOR = "."
    "The sign which defines in which folder a key is located"

    local_vault: DataStagVault = None  # The local vault instance

    def __init__(self):
        """
        Initializer
        """
        self.lock = RLock()
        self.start_time: int = int(time.time())
        self.last_garbage_collection_time = self.start_time - 1
        self.deprecating_elements: dict[int, list[DataStagElement]] = defaultdict(list)
        self.deprecation_stepping = 0
        self.global_dictionary: dict[str, DataStagElement] = {}
        "A dictionary containing all elements"
        self.folders: dict[str, dict] = defaultdict(dict)
        "A folder based more fine grained search index"

    @classmethod
    def get_local_vault(cls) -> "DataStagVault":
        """
        Returns the local vault instance
        """
        return cls.local_vault

    @staticmethod
    def get_server_up_time() -> float:
        """
        Get the server's working time to compute the deprecation of elements
        :return: Time offset since start in seconds
        """
        return time.time()

    def push(
        self,
        name: str,
        data: list[StagDataTypes],
        timeout_s: float | None = None,
        index=-1,
    ) -> int:
        """
        Appends an element at the end of a list
        :param name: The element's name
        :param data: The data to be added. See StagDataTypes for supported types
        :param timeout_s: The timeout for automatic deletion in seconds
        :param index: The index at which the elements shall be inserted. By default at the end.
        :return: The new length of the list
        """
        self.collect_garbage()
        with self.lock:
            list_handle: DataStagList | None = self._get_list_instance(name)
            if list_handle is None:
                assert not self.exists(name)
                list_handle = DataStagList(vault=self)
                self._register_element(name, list_handle)
            element_list = []
            for value in data:
                element = DataStagElement(self)
                dep_time = (
                    None if timeout_s is None else self.get_server_up_time() + timeout_s
                )
                element.parent = list_handle
                if dep_time is not None:
                    self._update_deprecating_element(element, dep_time)
                element.set_value(value, dep_time)
                element_list.append(element)
            return list_handle.add_elements(
                element_list, index=index, deprecation_time=dep_time
            )

    def pop(
        self, name: str, default: StagDataReturnTypes = None, index: int = 0
    ) -> StagDataReturnTypes:
        """
        Tries to remove an element at the beginning of a list
        :param name: The name's list
        :param default: The default return value if the list is empty or does not exist
        :param index: The index from which the element shall be "popped". By default from the front
        :return: The element which was removed
        """
        with self.lock:
            list_handle: DataStagList | None = self._get_list_instance(name)
            if list_handle is None:
                return default
            uptime = (
                self.get_server_up_time() if list_handle.objects_with_timeout else None
            )
            element = list_handle.pop_element(index=index, deprecation_time=uptime)
            if len(list_handle.list_elements) == 0:
                self.delete(name)
            if element is None:
                return default
            return element.get_value()

    def set(
        self, name: str, data: StagDataTypes, timeout_s: float | None = None
    ) -> bool:
        """
        Stores a named element in the database
        :param name: The element's name
        :param data: The data to be added. See StagDataTypes for supported types
        :param timeout_s: The timeout for automatic deletion
        :return: True on success
        """
        self.collect_garbage()
        with self.lock:
            element = self._get_element_by_name(name)
            assert (
                element is None or element.simple
            )  # Do not silently override lists or advanced sets
            if element is None:
                element = DataStagElement(self)
                element.name = name
                self._register_element(name, element)
            if timeout_s is not None:
                dep_time = self.get_server_up_time() + timeout_s
                self._update_deprecating_element(element, dep_time)
                element.set_value(data, deprecation_time=dep_time)
            else:
                element.set_value(data)
            return True

    def add(
        self,
        name: str,
        value: float | int = 1,
        timeout_s: float | None = None,
        default=0,
    ) -> float | int:
        """
        Adds given value to the element stored in the database. If it does not exist yet, it will be initialized
        with default.
        :param name: The element's name
        :param value: The value to be added
        :param timeout_s: The timeout for automatic deletion
        :param default: The default value
        :return: The new value
        """
        with self.lock:
            data = self.get(name, None)
            if data is None:
                new_value = default + value
                self.set(name, new_value, timeout_s=timeout_s)
                return new_value
            new_value = data + value
            self.set(name, new_value)
            return new_value

    def get(
        self, name: str, default: StagDataReturnTypes = None
    ) -> StagDataReturnTypes:
        """
        Tries to read an element from the database
        :param name: The element's name
        :param default: The default return value if the element does not exist
        :return: The element
        """
        with self.lock:
            element = self._get_element_by_name(name)
            if element is None:
                return default
            if element.deprecation_time is not None:
                if self.get_server_up_time() >= element.deprecation_time:
                    self._delete_element(name)
                    return None
            return element.get_value()

    def get_ex(
        self, name: str, default: StagDataReturnTypes = None, version_counter=-1
    ) -> (int, StagDataReturnTypes):
        """
        Tries to read an element from the database. Allows to add a version check so only data will be returned if
        it changed since the last get_ex.
        :param name: The element's name
        :param default: The default return value if the element does not exist
        :param version_counter: If set then a value will only be returned if the element's update counter does not match
        :return: The element's version, The element
        """
        with self.lock:
            element = self._get_element_by_name(name)
            if element is None:
                return 0, default
            if element.deprecation_time is not None:
                if self.get_server_up_time() >= element.deprecation_time:
                    self._delete_element(name)
                    return 0, None
                # Return nothing if the content did not change
            if version_counter != -1 and element.version_counter == version_counter:
                return version_counter, None
            return element.version_counter, element.get_value()

    def find(
        self,
        mask: str,
        limit: int = 100,
        relative_names: bool = False,
        recursive: bool = False,
    ):
        """
        Finds a list of elements by name
        :param mask: The search mask. If it contains a folder the mask is only applied to the nested element
        :param limit: The maximum count of entries
        :param relative_names: Defines if the relative names shall be returned
        :param recursive: Defines if the search shall continue recursive
        :return: A list of elements of all valid elements matching the search mask
        """
        uptime = self.get_server_up_time()
        with self.lock:
            folder_name, rel_name = self._split_folder_and_name(mask)
            if folder_name not in self.folders:
                return []
            folder = self.folders[folder_name]
            key_list = list(folder.keys())
            key_list = fnmatch.filter(key_list, rel_name)
            global_key_list = [
                self._get_global_name(folder_name, key) for key in key_list
            ]
            if not relative_names:
                key_list = global_key_list
                key_list = [
                    key
                    for key in key_list
                    if self.global_dictionary[key].deprecation_time is None
                    or self.global_dictionary[key].deprecation_time > uptime
                ]
            else:
                key_list = [
                    key
                    for key, g_key in zip(key_list, global_key_list)
                    if self.global_dictionary[g_key].deprecation_time is None
                    or self.global_dictionary[g_key].deprecation_time > uptime
                ]
            if limit != -1 and len(key_list) > limit:
                key_list = key_list[0:limit]
            if recursive:
                sub_folders = self.get_sub_folders(folder_name, recursive=True)
                for cur_sub_folder in sub_folders:
                    new_keys = self.find(cur_sub_folder + ".*", recursive=False)
                    if relative_names:
                        new_keys = [key[len(folder_name) + 1 :] for key in new_keys]
                        key_list += new_keys
                    else:
                        key_list += new_keys
        return key_list

    def get_sub_folders(self, name, recursive=True):
        """
        Returns all sub folders of folder_name

        :param name: The main folder
        :param recursive: Defines if the search shall be recursive.
        :return: The list of all nested folders
        """
        sub_folder_set = []
        with self.lock:
            search_mask = name + "."
            for element in self.folders:
                if element.startswith(search_mask):
                    if recursive:  # add all with shared root?
                        sub_folder_set.append(element)
                    else:  # add just direct child elements?
                        rest = element[0 : len(search_mask)]
                        if "." not in rest:
                            sub_folder_set.append(element)
        return list(sub_folder_set)

    def get_values_by_name(self, mask: str, limit: int = 100, flat: bool = True):
        """
        Returns the data of a set of elements by name.

        :param mask: The search mask. If it contains a folder the mask is only applied to the nested element
        :param limit: The maximum count of entries
        :param flat: Returns a list of all values received without providing the element names
        :return: A list containing the data and names of all valid elements
        """
        with self.lock:
            names = self.find(mask, limit)
            if flat:
                results = [
                    self.global_dictionary[name].get_value()
                    for name in names
                    if self.global_dictionary[name].simple
                ]
            else:
                results = [
                    {"name": name, "value": self.global_dictionary[name].get_value()}
                    for name in names
                    if self.global_dictionary[name].simple
                ]
            return results

    def llen(self, name: str) -> int:
        """
        Tries to retrieve the data of a list

        :param name: The list's name
        :return: The list length's if it does exist. Otherwise 0.
        """
        with self.lock:
            list_handle: DataStagList | None = self._get_list_instance(name)
            if list_handle is None:
                return 0
            if list_handle.objects_with_timeout:
                list_handle.collect_garbage(self.get_server_up_time())
            if len(list_handle.list_elements) == 0:
                self.delete(name)
                return 0
            return len(list_handle.list_elements)

    def lelements(self, name: str, start: int, end: int | None) -> list[StagDataTypes]:
        """
        Tries to receive a list of elements from the vault

        :param name: The list's name
        :param start: The first element's index
        :param end: The stop index (not included anymore). -1 = end of the list
        :return: The list's content in given range
        """
        with self.lock:
            list_handle = self._get_list_instance(name)
            if list_handle is None:
                return []
            uptime = (
                self.get_server_up_time() if list_handle.objects_with_timeout else None
            )
            result = list_handle.get_elements(start, end, time_s=uptime)
            if len(list_handle.list_elements) == 0:
                self.delete(name)
            return result

    def exists(self, name: str) -> bool:
        """
        Verifies if given element exists

        :param name: The element's name
        :return: True if the element exists
        """
        with self.lock:
            element = self._get_element_by_name(name, deprecation_time=-1)
            return element is not None

    def delete(self, name: str) -> bool:
        """
        Deletes an element
        :param name: The element's name
        :return: True on success
        """
        return self._delete_element(name)

    def delete_multiple(self, search_masks: list[str], recursive: bool = False) -> int:
        """
        Deletes a set of elements.

        :param search_masks: The element's names or search masks. May not point directly to the root directory
        :param recursive: Defines if the search shall be executed recursive
        :return: The count of removed elements
        """
        with self.lock:
            total = 0
            for cur_mask in search_masks:
                if len(cur_mask) == 0 or cur_mask[0] == "*" or "." not in cur_mask:
                    continue
                elements = self.find(cur_mask, recursive=recursive)
                for cur_element in elements:
                    if self._delete_element(cur_element):
                        total += 1
        return total

    def _get_element_by_name(
        self, name: str, deprecation_time: float | None = None
    ) -> DataStagElement | None:
        """
        Tries to retrieve a database element

        :param name: The element's name
        :param deprecation_time: The server uptime in seconds. If provided the
            element will be deleted if it timed out.
        """
        element = self.global_dictionary.get(name, None)
        if element is None:
            return None
        if element.deprecation_time is not None and deprecation_time is not None:
            if deprecation_time == -1:
                deprecation_time = self.get_server_up_time()
            if deprecation_time >= element.deprecation_time:
                self._delete_element(name)
                return None
        return element

    def _get_list_instance(self, name: str) -> DataStagList | None:
        """
        Tries to retrieve the element of the type list

        :param name: The element's name
        :return:
        """
        element = self._get_element_by_name(name)
        if isinstance(element, DataStagList):
            return element
        return None

    def _get_folder(self, name: str) -> str:
        """
        Returns the element's folder name defined by slashes

        :param name: The elements name
        :return: The folder, "" if none
        """
        index = name.rfind(self.FOLDER_SEPARATOR)
        if index == -1:
            return ""
        else:
            return name[0:index]

    def _split_folder_and_name(self, name: str) -> (str, str):
        """
        Returns the element's folder name defined by slashes

        :param name: The elements name
        :return: The folder and file name
        """
        folder_name = self._get_folder(name)
        if len(folder_name) > 0:
            return folder_name, name[len(folder_name) + 1 :]
        else:
            return "", name

    def _delete_element(self, name: str) -> bool:
        """
        Deletes an element from the global database

        :param name: The element's name
        :return: True on success
        """
        if name in self.global_dictionary:
            # remove from folder index
            folder_name, rel_name = self._split_folder_and_name(name)
            folder = self.folders[folder_name]
            del folder[rel_name]
            # remove empty folders
            if len(folder) == 0:
                del self.folders[folder_name]
            element = self.global_dictionary[name]
            if element.deprecation_time is not None:
                self._remove_from_deprecation_list(element)
            # remove from global index
            del self.global_dictionary[name]
            return True
        return False

    def _register_element(self, name: str, element: DataStagElement):
        """
        Registers a new element in the global map and the search tree

        :param name: The element's name
        :param element: The element
        """
        # register in global index
        self.global_dictionary[name] = element
        # register in folder index
        folder_name, rel_name = self._split_folder_and_name(name)
        self.folders[folder_name][rel_name] = element

    def _get_round_deprecation_time(self, dep_time: float):
        """
        Returns the deprecation time rounded up to the next second as integer

        :param dep_time: The deprecation time
        :return: Deprecation time in seconds
        """
        return int(dep_time) + self.deprecation_stepping

    def _remove_from_deprecation_list(self, element: DataStagElement):
        """
        Checks whether the element was already in a deprecation list and removes
        if from that one

        :param element: The element
        :return: True if the element was already existing and had to be removed
        """
        if element.deprecation_time is not None:
            prev_dep_time_round = self._get_round_deprecation_time(
                element.deprecation_time
            )
            prev_list = self.deprecating_elements[prev_dep_time_round]
            if element in prev_list:
                prev_list.remove(element)
                if len(prev_list) == 0:
                    del self.deprecating_elements[prev_dep_time_round]
                    return True
        return False

    def _update_deprecating_element(
        self, element: DataStagElement, dep_time: float = None
    ):
        """
        Registers the element in the deprecation registry so it can
        automatically be destroyed once it's outdated

        :param element: The element
        :param dep_time: The element's new deprecation time
        """
        self._remove_from_deprecation_list(element)
        dep_time_round = self._get_round_deprecation_time(dep_time)
        self.deprecating_elements[dep_time_round].append(element)

    def collect_garbage(self) -> bool:
        """
        Executes a garbage collection removing outdated elements

        :return: True if at least one time interval passed
        """
        with self.lock:
            cur_time = time.time()
            collection_time = int(cur_time) - 1
            if not collection_time > self.last_garbage_collection_time:
                return False
            while self.last_garbage_collection_time < collection_time:
                self.last_garbage_collection_time += 1
                cur_time_offset = self.last_garbage_collection_time
                if cur_time_offset not in self.deprecating_elements:
                    continue
                elements = self.deprecating_elements[cur_time_offset]
                while len(elements):
                    cur_element = elements[0]
                    if cur_element.parent:  # unnamed element with parent
                        if isinstance(cur_element.parent, DataStagList):
                            parent_list: DataStagList = cur_element.parent
                            if cur_element in parent_list.list_elements:
                                parent_list.list_elements.remove(cur_element)
                            elements.remove(cur_element)
                    elif cur_element.name is not None:
                        self._delete_element(cur_element.name)
                    elements = self.deprecating_elements[cur_time_offset]
                if cur_time_offset in self.deprecating_elements:
                    # in case the list did not empty itself yet
                    del self.deprecating_elements[cur_time_offset]
                    # delete key
        return True

    def get_status(self, advanced: bool = False):
        """
        Returns the database status
        :param advanced: Defines if advanced details shall be received as well
        :return: A dictionary containing the status
        """
        with self.lock:
            result = {
                "elementCount": len(self.global_dictionary),
                "folderCount": len(self.folders),
                "deprecationGroups": len(self.deprecating_elements),
                "startTime": self.start_time,
                "totalUpTime": time.time() - self.start_time,
            }
            if advanced:
                result["deprecationGroupNames"] = list(self.deprecating_elements.keys())
                result["lastGarbageCollection"] = self.last_garbage_collection_time
            return result

    def _get_global_name(self, folder_name, rel_name):
        """
        Returns the global element name
        :param folder_name: The folder name
        :param rel_name: The relative element name
        :return: Combined global element name
        """
        if folder_name != "":
            return folder_name + self.FOLDER_SEPARATOR + rel_name
        else:
            return rel_name


DataStagVault.local_vault = DataStagVault()
