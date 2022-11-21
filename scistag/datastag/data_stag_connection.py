from __future__ import annotations
import time
from threading import RLock

import io
import numpy as np
import base64
import requests
from .data_stag_common import StagDataTypes, StagDataReturnTypes
from .data_stag_vault import DataStagVault


class DataStagConnection:
    """
    Defines a connection to a DataStack vault - locally or remote
    """

    # Definition of parameters
    _DATA = "data"
    _DEFAULT = "default"
    _TYPE = "_dstype"
    _VALUE = "_dsvalue"
    _INDEX = "index"
    _TIME_OUT = "timeOut"
    _NAME = "name"
    _START = "start"
    _END = "end"
    _ELEMENTS = "elements"
    _SEARCH_MASKS = "searchMasks"
    _MASK = "mask"
    _LIMIT = "limit"
    _RELATIVE_NAMES = "relativeNames"
    _RECURSIVE = "recursive"
    _FLAT = "flat"
    _ADVANCED = "advanced"
    _VERSION_COUNTER = "versionCounter"

    _TYPE_BYTES = "bytes"
    _TYPE_NUMPY = "numpy"

    # Definition of server commands
    _COMMAND = "com"
    _COMMAND_PUSH = "push"
    _COMMAND_POP = "pop"
    _COMMAND_LELEMENTS = "lelements"
    _COMMAND_SET = "set"
    _COMMAND_ADD = "add"
    _COMMAND_GET = "get"
    _COMMAND_GET_EX = "getEx"
    _COMMAND_LLEN = "llen"
    _COMMAND_EXISTS = "exists"
    _COMMAND_DELETE = "delete"
    _COMMAND_DELETE_MULTIPLE = "deletemulti"
    _COMMAND_FIND = "find"
    _COMMAND_GET_VALUES_BY_NAME = "getValuesByName"
    _COMMAND_STATUS = "status"
    _COMMAND_COLLECT_GARBAGE = "collectGarbage"
    _TIMESTAMP_IDENTIFIER = ":timeStamp"
    _COUNTER_IDENTIFIER = ":counter"
    """
    Name of a timestamp neighbour entry in which the time when an
    entry was written is stored
    """

    def __init__(self, url: str = "", local=True,
                 _request_client: "FlaskClient" = None):
        """
        Initializer

        :param url: The connection url of a remote server
        :param local: Defines if the local in memory database shall be used
        :param _request_client: For unit tests only. Uses Flask's internal test
            client to test the API.
        """
        self.local = local
        'Defines if a local storage is being used'
        self.vault: DataStagVault | None = DataStagVault.local_vault
        'Link to the local data vault'
        self.target_url: str = url
        'The target url (when not using a local db)'
        self.request_client: "FlaskClient" = _request_client
        'When testing locally this links to the local test client'
        self.transaction_lock = 0
        self._cur_transaction: "DataStagTransaction" | None = None
        "The current transaction"
        self.lock = RLock()

    def start_transaction(self):
        """
        Starts a new transaction. All write operations will be bundled and
            executed in a single lock.

        Use like:
        `with my_connection.start_transaction(): ...`
        :return: The transaction object
        """
        return DataStagTransaction(self)

    def ts_lock(self, target: "DataStagTransaction"):
        """
        Locks the access to the vault and bundles upcoming write events

        :param target: The current transaction
        """
        with self.lock:
            self.transaction_lock += 1
            self._cur_transaction = target
            if self.local and self.transaction_lock == 1:
                self.vault.lock.acquire()

    def ts_unlock(self):
        """
        Unlocks the access to the vault and bundles upcoming write events
        """
        with self.lock:
            self.transaction_lock -= 1
            if self.transaction_lock == 0:
                if self.local:
                    self.vault.lock.release()
                    self._cur_transaction = None
                elif self._cur_transaction is not None:
                    cur_transaction: "DataStagTransaction" = \
                        self._cur_transaction
                    self._cur_transaction = None
                    self._execute_remote(
                        cur_transaction.commands)
                    # Execute all commands in one go

    def push(self, name: str, data: list[StagDataTypes] | StagDataTypes,
             timeout_s: float | None = None,
             index: int = -1) -> int:
        """
        Inserts an element at the beginning of a list

        :param name: The element's name
        :param data: The data to be added. See StagDataTypes for supported types
        :param timeout_s: The timeout for automatic deletion
        :param index: The index at which the data shall be inserted.
            By default at the end.
        :return: The new length of the list
        """
        if not isinstance(data, list):
            data = [data]
        if self.local:
            return self.vault.push(name, data=data, timeout_s=timeout_s,
                                   index=index)
        elements = [self.data_to_json(element) for element in data]
        return self._verify_result(
            self._execute_remote({self._COMMAND: self._COMMAND_PUSH,
                                  self._NAME: name,
                                  self._ELEMENTS: elements,
                                  self._TIME_OUT: timeout_s,
                                  self._INDEX: index}), supported_types=[int])

    def pop(self, name: str, default: StagDataReturnTypes = None,
            index: int = 0) -> StagDataReturnTypes:
        """
        Tries to remove an element at the beginning of a list

        :param name: The name's list
        :param default: The default return value if the list is empty or does
            not exist
        :param index: The index from which the data shall be received.
            By default at the front
        :return: The element which was removed
        """
        if self.local:
            return self.vault.pop(name, default=default, index=index)
        result = self._verify_ct_result(self._execute_remote(
            {self._COMMAND: self._COMMAND_POP, self._NAME: name,
             self._INDEX: index}))
        if result is None:
            return default
        return result

    def lelements(self, name: str, start: int = 0, end: int | None = None) -> \
            list[StagDataTypes]:
        """
        Tries to receive a list of elements from the vault

        :param name: The list's name
        :param start: The first element's index
        :param end: The stop index (not included anymore). -1 = end of the list
        :return: The list's content in given range
        """
        if self.local:
            return self.vault.lelements(name, start, end)
        response: list = self._execute_remote(
            {self._COMMAND: self._COMMAND_LELEMENTS,
             self._NAME: name,
             self._START: start,
             self._END: end})
        if response is None or not isinstance(response, list):
            return []
        elements = response
        result = []
        for element in elements:
            result.append(self.json_to_data(element))
        return result

    def llen(self, name: str) -> int:
        """
        Tries to retrieve the data of a list

        :param name: The list's name
        :return: The list length's if it does exist. Otherwise 0.
        """
        if self.local:
            return self.vault.llen(name)
        response: int = self._verify_int_result(
            self._execute_remote(
                {self._COMMAND: self._COMMAND_LLEN, self._NAME: name}))
        return response if response is not None else 0

    def set(self, name: str, data: StagDataTypes,
            timeout_s: float | None = None) -> bool:
        """
        Stores a named element in the database

        :param name: The element's name
        :param data: The data to be added. See StagDataTypes for supported types
        :param timeout_s: The timeout for automatic deletion
        :return: True on success
        """
        if self.local:
            return self.vault.set(name, data, timeout_s)
        return self._verify_bool_result(
            self._execute_remote(
                {self._COMMAND: self._COMMAND_SET, self._NAME: name,
                 self._DATA: self.data_to_json(data),
                 self._TIME_OUT: timeout_s}))

    def set_ts(self, name: str, data: StagDataTypes,
               timeout_s: float | None = None,
               timestamp: float | None = None) -> bool:
        """
        Stores a named element in the database and adds a timestamp to it in a
        neighbour entry named :timeStamp

        :param name: The element's name
        :param data: The data to be added. See StagDataTypes for supported types
        :param timeout_s: The timeout for automatic deletion
        :param timestamp: A custom timestamp. If None is provided the current
            time will be used
        :return: True on success
        """
        with self.start_transaction():
            success = self.set(name, data, timeout_s)
            if timestamp is None:
                timestamp = time.time()
            return self.set(name + self._TIMESTAMP_IDENTIFIER, timestamp,
                            timeout_s) and success

    def get_ts(self, name: str, default: float = 0.0) -> float:
        """
        Returns an object's update time stamp (if it was set via set_ts)

        :param name: The element's name
        :param default: The default return value
        :return: The timestamp on success
        """
        return self.get(name + self._TIMESTAMP_IDENTIFIER, default=default)

    def get_ts_modified(self, name: str, timestamp: float = 0.0) -> (
            float, StagDataReturnTypes):
        """
        Returns the object if it was modified since timestamp

        :param name: The element's name
        :param timestamp: The previous timestamp
        :return: Returns the new value if the data was modified.

            * On success: The timestamp or counter, the data on success
            * On failure: The old timestamp, None
        """
        new_ts = self.get(name + self._TIMESTAMP_IDENTIFIER, default=0.0)
        if timestamp != new_ts:
            return new_ts, self.get(name, default=None)
        return timestamp, None

    def get(self, name: str,
            default: StagDataReturnTypes = None) -> StagDataReturnTypes:
        """
        Tries to read an element from the database

        :param name: The element's name
        :param default: The default return value if the element does nto exist
        :return: The element
        """
        if self.local:
            return self.vault.get(name, default)
        response: dict = self._execute_remote({self._COMMAND: self._COMMAND_GET,
                                               self._NAME: name})
        data = self.json_to_data(response)
        return data if data is not None else default

    def get_ex(self, name: str, default: StagDataReturnTypes = None,
               version_counter=-1) -> (int, StagDataReturnTypes):
        """
        Tries to read an element from the database. Allows to add a version
        check so only data will be returned if it changed since the last get_ex.

        :param name: The element's name
        :param default: The default return value if the element does not exist
        :param version_counter: If set then a value will only be returned if
        the element's update counter does not match
        :return: The element's version, The element
        """
        if self.local:
            return self.vault.get_ex(name, default,
                                     version_counter=version_counter)
        response: dict = self._execute_remote(
            {self._COMMAND: self._COMMAND_GET_EX,
             self._NAME: name,
             self._VERSION_COUNTER: version_counter})
        result = self.json_to_data(response)
        return result[0], result[1]

    def add(self, name: str, value: [float, int] = 1,
            timeout_s: float | None = None, default=0) -> int | float:
        """
        Adds given value to the element stored in the database. If it does
        not exist yet, it will be initialized with default.

        :param name: The element's name
        :param value: The value to be added. 1 by default.
        :param timeout_s: The timeout for automatic deletion
        :param default: The default value
        :return: The new value
        """
        if self.local:
            return self.vault.add(name, value, timeout_s, default=default)
        return self._verify_result(
            self._execute_remote(
                {self._COMMAND: self._COMMAND_ADD, self._NAME: name,
                 self._VALUE: self.data_to_json(value),
                 self._TIME_OUT: timeout_s,
                 self._DEFAULT: default}), supported_types=[float, int])

    def exists(self, name: str) -> bool:
        """
        Verifies if given element exists in the database.

        :param name: The element's name
        :return: True if the element exists
        """
        if self.local:
            return self.vault.exists(name)
        response: int = self._verify_bool_result(
            self._verify_bool_result(self._execute_remote(
                {self._COMMAND: self._COMMAND_EXISTS, self._NAME: name})))
        return response if response is not None else False

    def delete(self, name: str) -> bool:
        """
        Deletes an element by its name

        :param name: The element's name.
        :return: True on success
        """
        if self.local:
            return self.vault.delete(name)
        response: int = self._verify_bool_result(
            self._verify_bool_result(self._execute_remote(
                {self._COMMAND: self._COMMAND_DELETE, self._NAME: name})))
        return response if response is not None else False

    def delete_multiple(self, search_masks: list[str],
                        recursive: bool = False) -> int:
        """
        Deletes a set of elements using a search mask

        :param search_masks: The element's names or search masks. May not point
            directly to the root directory
        :param recursive: Defines if the search shall be executed recursive
        :return: The count of removed elements
        """
        if self.local:
            return self.vault.delete_multiple(search_masks, recursive=recursive)
        response: int = self._verify_int_result(
            self._verify_int_result(self._execute_remote(
                {self._COMMAND: self._COMMAND_DELETE_MULTIPLE,
                 self._SEARCH_MASKS: search_masks,
                 self._RECURSIVE: recursive})))
        return response if response is not None else 0

    def find(self, mask: str, limit: int = 100, relative_names: bool = False,
             recursive: bool = False) -> list[
        StagDataTypes]:
        """
        Finds a list of elements by name

        :param mask: The search mask. If it contains a folder the mask is only
            applied to the nested element
        :param limit: The maximum count of entries
        :param relative_names: Defines if the relative names shall be returned
        :param recursive: Defines if the search shall be executed recursive
        :return: A list of elements of all valid elements matching the search
            mask
        """
        if self.local:
            return self.vault.find(mask=mask, limit=limit,
                                   relative_names=relative_names,
                                   recursive=recursive)
        response: list = self._execute_remote(
            {self._COMMAND: self._COMMAND_FIND, self._MASK: mask,
             self._LIMIT: limit, self._RELATIVE_NAMES: relative_names,
             self._RECURSIVE: recursive})
        if response is None:
            return []
        return [self.json_to_data(element) for element in response]

    def get_values_by_name(self, mask: str, limit: int = 100,
                           flat: bool = True):
        """
        Returns the data of a set of elements by name.

        :param mask: The search mask. If it contains a folder the mask is only
            applied to the nested element
        :param limit: The maximum count of entries
        :param flat: Returns a list of all values received without providing the
            element names
        :return: A list containing the data and names of all valid elements
        """
        if self.local:
            return self.vault.get_values_by_name(mask=mask, limit=limit,
                                                 flat=flat)
        response = self._execute_remote(
            {self._COMMAND: self._COMMAND_GET_VALUES_BY_NAME,
             self._LIMIT: limit,
             self._MASK: mask,
             self._FLAT: flat})
        if response is None:
            return []
        if flat:
            return [self.json_to_data(element) for element in response]
        response: list[dict]
        return [{"name": element["name"],
                 "value": self.json_to_data(element["value"])} for element in
                response]

    def get_status(self, advanced: bool = False):
        """
        Returns the database status

        :param advanced: Defines if advanced details shall be received as well
        :return: A dictionary containing the status
        """
        if self.local:
            return self.vault.get_status(advanced=advanced)
        response = self._execute_remote(
            {self._COMMAND: self._COMMAND_STATUS, self._ADVANCED: advanced})
        return self._verify_dict_result(response)

    def collect_garbage(self) -> bool:
        """
        Implicit garbage collection request

        :return: True if at least one time interval passed and something could
            get collected
        """
        if self.local:
            return self.vault.collect_garbage()
        return self._verify_bool_result(self._execute_remote(
            {self._COMMAND: self._COMMAND_COLLECT_GARBAGE}))

    def _execute_remote(self, command: dict | list) -> \
            dict | list | str | float | int | bool | None:
        """
        Executes a command remotely and returns it's result

        :param command: The command or list of commands
        :return: The result
        """
        with self.lock:
            if self._cur_transaction is not None:
                # If a transaction is in progress, collect changes first
                self._cur_transaction.add_command(command)
                return True  # We can not receive single response
        if self.request_client is not None:  # Flask UT
            response = self.request_client.post("/run", json=command)
            json_data = response.get_json()
        else:
            response = requests.post(f"{self.target_url}/run", json=command)
            json_data = response.json()
        if json_data is not None and isinstance(json_data, list):
            # return the single results as a list
            result = [ele for ele in json_data if
                      ele is not None and 'data' in ele]
            return result
        return json_data['data'] if json_data is not None else None

    @classmethod
    def _verify_result(cls, result, supported_types: list) -> \
            int | float | bool | str | dict | bytes | np.ndarray | None:
        """
        Verifies if the result is of a given type

        :param result: The result
        :param supported_types: The list of types which are allowed for this
            time
        :return: The result value if the type is correct, otherwise None
        """
        result = cls.json_to_data(result)
        if type(result) in supported_types:
            return result
        return None

    def _verify_int_result(self, result: object) -> int:
        """
        Verifies if the result is of type int

        :param result: The result
        :return: The result value if the type is an integer, otherwise None
        """
        result = self._verify_result(result, [int])
        return result if result is not None else 0

    def _verify_bool_result(self, result: object) -> bool:
        """
        Verifies if the result is of type bool

        :param result: The result
        :return: The result value if the type is a bool, otherwise None
        """
        result = self._verify_result(result, [bool])
        return result if result is not None else False

    def _verify_dict_result(self, result: object) -> dict:
        """
        Verifies if the result is of type dict

        :param result: The result
        :return: The result value if the type is a dict, otherwise None
        """
        result = self._verify_result(result, [dict])
        return result if result is not None else {}

    def _verify_ct_result(self, result: dict) -> int:
        """
        Verifies if the result is of any allowed storable type

        :param result: The result
        :return: The result value if the type is allowed, otherwise None
        """
        return self._verify_result(result, [int, float, bool, str, dict, bytes,
                                            np.ndarray])

    @classmethod
    def json_to_data(cls, data) -> StagDataReturnTypes:
        """
        Converts an element converted to JSOn back to it's original type.
        Special types, e.g. binary representations are flagged as those using
        a _TYPE and a _VALUE element in a dictionary.

        :param data: The result
        :return: The data in the original type, e.g. byte or np.ndarray
        """
        if type(data) in [int, bool, float, str, bytes]:
            return data
        if isinstance(data, list):
            return [cls.json_to_data(element) for element in data]
        if not isinstance(data, dict):
            return None
        data: dict
        if cls._TYPE in data and cls._VALUE in data:
            dtype = data.get(cls._TYPE)
            if dtype == cls._TYPE_BYTES:
                return base64.b64decode(data[cls._VALUE])
            elif dtype == cls._TYPE_NUMPY:
                decoded = base64.b64decode(data[cls._VALUE])
                return np.load(io.BytesIO(decoded))
        return data

    @classmethod
    def data_to_json(cls, data: StagDataTypes) -> StagDataReturnTypes:
        """
        Converts data of a binary type, e.g. np.ndarray or bytes to a JSON
        representation

        :param data: The data
        :return: The JSON representation which can decoded on the receiver side
            again using json_to_data
        """
        if type(data) in [int, bool, float, str, dict]:
            return data
        if type(data) in [list]:
            return [cls.data_to_json(element) for element in data]
        if isinstance(data, bytes):
            encoded = base64.b64encode(data).decode('ascii')
            return {cls._TYPE: cls._TYPE_BYTES, cls._VALUE: encoded}
        if isinstance(data, np.ndarray):
            output = io.BytesIO()
            data: np.ndarray
            np.save(output, data)
            value = output.getvalue()
            encoded = base64.b64encode(value).decode('ascii')
            return {cls._TYPE: cls._TYPE_NUMPY, cls._VALUE: encoded}


class DataStagTransaction:
    """
    Defines a transaction which blocks the access to a vault if a full
    transaction is executed
    """

    def __init__(self, connection: "DataStagConnection"):
        super().__init__()
        self.connection = connection
        self.commands = []

    def __enter__(self):
        self.connection.ts_lock(self)

    def __exit__(self, class_type, value, traceback):
        self.connection.ts_unlock()

    def add_command(self, command: dict | list):
        """
        Adds a command to the queue
        :param command: The command or list of commands
        """
        self.commands.append(command)
