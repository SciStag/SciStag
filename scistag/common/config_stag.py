from __future__ import annotations
import io
import json
import os
from threading import RLock
import copy
from typing import Union

from scistag.filestag import FileStag

ConfigValueTypes = Union[str, int, float, dict, list, bool]
"The types supported to store and receive configuration"


class ConfigStag:
    access_lock = RLock()
    "Multithreading access lock"
    root_branch = {}
    "The root branch"

    @classmethod
    def _get_branch(
        cls, cur_branch: dict, source: str | list[str], may_create=True
    ) -> dict | None:
        """
        Returns the branch for a specific path in the format mainBranch.subBranch.nextBranch.

        If may_create is set to true all missing branches in between will be created. If not and the path can not
        be resolved None will be returned.

        :param cur_branch: The current start branch
        :param source: The path to the dictionary, a list or a string separated by dots,
            e.g. azure.storage.connectionString
        :param may_create: Defines if the branch may be created if it does not exist yet
        :return: The dictionary for the branch
        """
        branches = source.split(".") if isinstance(source, str) else source
        if len(branches[0]) == 0:
            return cur_branch
        if branches[0] in cur_branch:
            next_branch = cur_branch[branches[0]]
        elif may_create:
            next_branch = {}
            cur_branch[branches[0]] = next_branch
        else:
            return None
        if len(branches) == 1:  # reached the last branch?
            return next_branch
        else:
            return cls._get_branch(next_branch, branches[1:], may_create=may_create)

    @classmethod
    def load_config_file(
        cls,
        source: str,
        base_branch: str = "",
        required=True,
        environment: str | None = None,
    ):
        """
        Loads a configuration file and attaches it to the global configuration tree

        :param source: The file source (accessible via FileStag)
        :param base_branch: The branch name to which this element shall be attached, separated by dots.
        :param required: Defines if an exception shall be raised if this file does not exist
        :param environment: If defined environment variables beginning with given shortcut will be imported.
            UnderScores will be replaced by dots. All variables will be imported relative to base_branch
        """
        with cls.access_lock:
            data = FileStag.load(source)
            if data is None:
                if environment is not None and len(environment) > 0:
                    cls.import_environment(base_branch, environment)
                if not required:
                    return
                raise FileNotFoundError(f"Could not load configuration from {source}")
            new_elements = json.load(io.BytesIO(data))
            if len(base_branch) == 0:
                tar_branch = cls.root_branch
            else:
                tar_branch = cls._get_branch(cls.root_branch, base_branch)
            tar_branch |= new_elements
        if environment is not None and len(environment) > 0:
            cls.import_environment(base_branch, environment)

    @classmethod
    def import_environment(cls, base_branch: str = "", environment: str = "SC_"):
        """
        Imports all environment variables beginning with environment into the configuration, starting at branch
            base_branch.

        All underscores in the name will automatically be replaced by dots.

        Example: SC_dataBase_connectionString is the environment variables name, our base_branch is "settings"
        and environment has the value ``"SC_"`` then the content will be stored in settings.dataBase.connectionString.

        If no parameters are passed automatically all variables beginning with SC_ will be imported into the main
        branch.

        :param base_branch: The branch in which the data shall be stored
        :param environment: The string with which the environment variables have to begin to be recognized
        """
        for item, value in os.environ.items():
            if item.startswith(environment):
                name_rest = item[len(environment) :]
                name_rest = name_rest.replace("_", ".").lower()
                if len(base_branch) > 1:
                    cls.set(base_branch + "." + name_rest, value)
                else:
                    cls.set(name_rest, value)

    @classmethod
    def set(cls, name: str, value: ConfigValueTypes) -> None:
        """
        Changes a single value in the configuration tree.

        Note that if you map an advanced type (such as a list of a dict) you will always receive a copy of the
        data to prevent accidental modifications via a reference.

        :param name: The value's name
        :param value: The new value
        """
        with cls.access_lock:
            path = name.split(".")
            if len(path[-1]) == 0:
                raise ValueError("Zero length identifier provided")
            tar_branch = cls.root_branch
            if len(path) > 1:
                tar_branch = cls._get_branch(tar_branch, path[0:-1])
            if isinstance(value, dict) or isinstance(value, list):
                tar_branch[path[-1]] = copy.deepcopy(value)
            else:
                tar_branch[path[-1]] = value

    @classmethod
    def get(cls, name: str, default_value=None) -> ConfigValueTypes:
        """
        Returns a single value from the configuration tree, a list or a dictionary of values from the configuration.

        Note that if you receive an advanced type (such as a list of a dict) you will always receive a copy of the
        data to prevent accidental modifications via a reference.

        :param name: The value's name
        :param default_value: The default value to return if the key does not exist
        :return: The current value
        """
        with cls.access_lock:
            path = name.split(".")
            if len(path[-1]) == 0:
                raise ValueError("Zero length identifier provided")
            tar_branch = cls.root_branch
            if len(path) > 1:
                tar_branch = cls._get_branch(tar_branch, path[0:-1], may_create=False)
            if tar_branch is None:
                return default_value
            result = tar_branch.get(path[-1], default_value)
            if isinstance(result, dict) or isinstance(result, list):
                return copy.deepcopy(result)
            return result

    @classmethod
    def map_environment(cls, environ_name, config_name) -> bool:
        """
        Maps a single value from an environment variable to a configuration value (if it was set).

        If the environment variable does not exist nothing will be changed.

        :param environ_name: The environment variable name (the source)
        :param config_name: The target name, e.g. azure.connection.credentials.connectionString
        :return: True if the variable was updated
        """
        if environ_name in os.environ:
            cls.set(config_name, os.environ.get(environ_name))
            return True
        return False
