"""
Defines the options for optional LogBuilder extensions such as support for graphs
"""
from __future__ import annotations

from pydantic import BaseModel

_KNOWN_EXTENSIONS = {"mermaid"}
"""The list of known extensions. Will be replaced by a dynamic registry in the future"""

MERMAID_EXTENSION = "mermaid"
"""The mermaid extension for Markdown - allows the creation of graphs using VisualLog"""


class ExtensionOptions(BaseModel):
    """
    Defines the optional extensions which shall be added to the log
    """

    extensions: set[str] = set()
    """Set of optional extensions"""

    additional_js: dict[str, bytes] = dict()
    """
    Additional JS files to be added to the log, their name and data 
    """

    additional_code: dict[str, bytes] = dict()
    """
    Additional code to be executed after the scripts were imported 
    """

    additional_css: dict[str, bytes] = dict()
    """
    Additional CSS files to be added to the log, their name and data 
    """

    def validate_options(self):
        """
        Validates the options and checks assumed fields are configured correctly
        """
        for element in self.extensions:
            if not self.verify_extension(element):
                return False
            self.setup_extension(element)

    def add(self, names: str | list[str] | set[str]) -> bool:
        """
        Adds one or multiple extensions

        :param names: The name or names of the extensions
        :return: True if all extensions could be found and added, false otherwise
        """
        if isinstance(names, str):
            names = {names}
        elif isinstance(names, list):
            names = set(names)
        self.extensions = self.extensions.union(names)
        return True

    def setup_extension(self, name: str):
        """
        Setups the extension with given name

        :param name: The extension's name
        """
        if name == MERMAID_EXTENSION:
            from chartstag.mermaid import get_mermaid_script
            self.additional_js[
                "mermaid_min.js"] = get_mermaid_script()
            self.additional_code[
                "mermaid"] = b"<script>mermaid.initialize({startOnLoad:true," \
                             b"flowchart:{htmlLabels:true}," \
                             b"securityLevel:'loose'})</script>"

    def verify_extension(self, name: str) -> bool:
        """
        Verifies if the extension is valid and can be added

        :param name: The extension's name
        :return: True on success
        """
        if name == MERMAID_EXTENSION:
            try:
                from chartstag.mermaid import get_mermaid_script
                return True
            except ModuleNotFoundError:
                return False
        return False
