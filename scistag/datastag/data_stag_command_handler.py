from __future__ import annotations
from typing import Callable
from scistag.datastag.data_stag_connection import DataStagConnection


class DataStagCommandHandler(DataStagConnection):
    """
    Maps http calls to the server to connection function calls
    """

    def __init__(self, local: bool = True):
        """
        Initializer

        :param local: Defines if the local connection shall be used.
        """
        super().__init__(local=local)
        self.commands: dict[str, Callable[[dict], dict]] = {
            self._COMMAND_SET: self._handle_set,
            self._COMMAND_GET: self._handle_get,
            self._COMMAND_GET_EX: self._handle_get_ex,
            self._COMMAND_ADD: self._handle_add,
            self._COMMAND_PUSH: self._handle_push,
            self._COMMAND_POP: self._handle_pop,
            self._COMMAND_LLEN: self._handle_llen,
            self._COMMAND_DELETE: self._handle_delete,
            self._COMMAND_DELETE_MULTIPLE: self._handle_delete_multiple,
            self._COMMAND_EXISTS: self._handle_exists,
            self._COMMAND_GET_VALUES_BY_NAME: self._handle_get_values_by_name,
            self._COMMAND_LELEMENTS: self._handle_lelements,
            self._COMMAND_FIND: self._handle_find,
            self._COMMAND_COLLECT_GARBAGE: self._handle_collect_garbage,
            self._COMMAND_STATUS: self._handle_status,
        }
        """
        Dictionary which maps the incoming commands to their corresponding
        functions
        """

    @classmethod
    def bundle_return(cls, data) -> dict:
        """
        Converts the data to a JSON compatible representation

        :param data: The data
        :return: The JSON compatible dictionary
        """
        conv_data = cls.data_to_json(data)
        return {cls._DATA: conv_data}

    def handle_command_data(
        self, command_data: dict | list
    ) -> dict | list[dict | None] | None:
        """
        Execute a single remote command or list of remote commands executed in
        the DataVault

        :param command_data: The command data
        :return: The commands return value
        """
        if isinstance(command_data, list):
            results = [self.handle_command_data(element) for element in command_data]
            return results
        command = command_data.get(self._COMMAND, "")
        if command in self.commands:
            return self.commands[command](command_data)
        return None

    def _handle_set(self, command: dict) -> dict:
        """
        Executes a set command which sets a single value in the vault

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        name = command.get(self._NAME)
        temp_value = command.get(self._DATA)
        value = self.json_to_data(temp_value)
        timeout = command.get(self._TIME_OUT)
        self.set(name=name, data=value, timeout_s=timeout)
        return self.bundle_return(True)

    def _handle_add(self, command: dict) -> dict:
        """
        Executes a set command which adds a given amount to a value

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        name = command.get(self._NAME)
        temp_value = command.get(self._VALUE)
        value = self.json_to_data(temp_value)
        timeout = command.get(self._TIME_OUT)
        default = command.get(self._DEFAULT)
        res = self.add(name=name, value=value, timeout_s=timeout, default=default)
        return self.bundle_return(res)

    def _handle_get(self, command: dict) -> dict:
        """
        Executes a get command which returns a variable's content

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        name = command.get(self._NAME)
        data = self.get(name, default=None)
        return self.bundle_return(data)

    def _handle_get_ex(self, command: dict) -> dict:
        """
        Executes an advanced get command which allows retrieving a value only
        if it changed

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        name = command.get(self._NAME)
        version_counter = command.get(self._VERSION_COUNTER)
        version, data = self.get_ex(name, default=None, version_counter=version_counter)
        return self.bundle_return([version, data])

    def _handle_push(self, command: dict) -> dict:
        """
        Executes a list push which adds one or multiple values to a list

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        name = command.get(self._NAME)
        data = command.get(self._ELEMENTS)
        data = [self.json_to_data(element) for element in data]
        index = command.get(self._INDEX, -1)
        timeout = command.get(self._TIME_OUT, None)
        result = self.push(name, data, timeout_s=timeout, index=index)
        return self.bundle_return(result)

    def _handle_pop(self, command: dict) -> dict:
        """
        Executes an advanced list pop which tries to retrieve a value from a
        list

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        name = command.get(self._NAME)
        index = command.get(self._INDEX, 0)
        result = self.pop(name, default=None, index=index)
        return self.bundle_return(result)

    def _handle_llen(self, command: dict) -> dict:
        """
        Executes a llen command which retrieves the length of a list

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        name = command.get(self._NAME)
        result = self.llen(name)
        return self.bundle_return(result)

    def _handle_delete(self, command: dict) -> dict:
        """
        Executes a delete command which deletes a single value

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        name = command.get(self._NAME)
        return self.bundle_return(self.delete(name))

    def _handle_delete_multiple(self, command: dict) -> dict:
        """
        Executes a delete_multiple command which deletes a list of values m
        atching a given mask

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        search_masks = command.get(self._SEARCH_MASKS)
        recursive = command.get(self._RECURSIVE, False)
        return self.bundle_return(
            self.delete_multiple(search_masks, recursive=recursive)
        )

    def _handle_exists(self, command: dict) -> dict:
        """
        Executes an exists command which returns if a value exists

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        name = command.get(self._NAME)
        return self.bundle_return(self.exists(name))

    def _handle_get_values_by_name(self, command: dict) -> dict:
        """
        Executes a get_values_by_name command which receives all values
        matching a given mask by name

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        mask = command.get(self._MASK)
        limit = command.get(self._LIMIT)
        flat = command.get(self._FLAT)
        results = self.get_values_by_name(mask=mask, limit=limit, flat=flat)
        if flat:
            return self.bundle_return(results)
        else:
            results: list[dict]
            return {
                self._DATA: [
                    {
                        "name": element["name"],
                        "value": self.json_to_data(element["value"]),
                    }
                    for element in results
                ]
            }

    def _handle_lelements(self, command: dict) -> dict:
        """
        Executes a lelements command which receives a set of elements in a
        given range from a list

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        name = command.get(self._NAME)
        start = command.get(self._START, 0)
        end = command.get(self._END, None)
        return self.bundle_return(self.lelements(name, start=start, end=end))

    def _handle_find(self, command: dict) -> dict:
        """
        Executes a find command which returns all values' names matching a
        given mask

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        mask = command.get(self._MASK)
        limit = command.get(self._LIMIT)
        relative_names = command.get(self._RELATIVE_NAMES, False)
        recursive = command.get(self._RECURSIVE, False)
        results = self.find(
            mask=mask, limit=limit, relative_names=relative_names, recursive=recursive
        )
        return self.bundle_return(results)

    def _handle_collect_garbage(self, command: dict) -> dict:
        """
        Executes a garbage collection

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        return self.bundle_return(self.collect_garbage())

    def _handle_status(self, command: dict) -> dict:
        """
        Executes a server status request checking the server's health status

        :param command: The command's parameters as dictionary
        :return: The response as dictionary
        """
        advanced = command.get(self._ADVANCED)
        return self.bundle_return(self.get_status(advanced=advanced))
