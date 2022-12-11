"""
Helper functions to handle environment variables and configuration files
"""
import os

from scistag.filestag import FileStag


class Env:
    """
    Environment helper class
    """

    @staticmethod
    def load_env_file(path: str, fail_silent: bool = False) -> dict:
        """
        Loads an environment file located at str and applies it

        The file is usually named .env and has the format key=value where a
        key value pair is defined per line.

        :param path: The file's path.
        :param fail_silent: If set no error will be risen if the file is
            missing.
        :return: A dictionary containing all key value pairs
        """
        content = FileStag.load_text(path)
        if content is None:
            if fail_silent:
                return {}
            raise FileNotFoundError(f"File {path} not found")
        content = content.replace("\r", "").split("\n")
        result_dict = {}
        for cur_line in content:
            if "#" in cur_line:
                cur_line = cur_line[0 : cur_line.index("#")]
            if "=" not in cur_line:
                raise AssertionError(f"No assignment found for {cur_line}")
            cur_line = cur_line.lstrip("'\" ").rstrip("\"' ")
            first_app = cur_line.index("=")
            key = cur_line[0:first_app]
            value = cur_line[first_app + 1 :]
            result_dict[key] = value
            os.environ[key] = value
        return result_dict

    @staticmethod
    def insert_environment_data(text: str):
        """
        Searches for double curly brackets inside string followed by env.
        All occurrences for which an environment exists will be replaced with
        the environment variables content.

        Example: https://{{env.username}}:{{env.password}}@myserver.com

        will insert the environment variables username and password inside
        the string.

        :param text: The text to search within
        :return: The string into which the environment variables were inserted
        """
        if "{{env." not in text:
            return text
        for key, value in os.environ.items():
            search_token = "{{env." + key + "}}"
            text = text.replace(search_token, value)
        return text
