import argparse

import sys

import scistag.addons
from scistag.addons import AddonManager
from scistag.addons.addon_manager import FEATURE_SIZE, FEATURE_INFO


class AddonCli:
    """
    Command line interface to install or remove addons

    Usage:
    python3 -m scistag.addons install [ADDON_NAME,ADDON_NAME,...]
    or
    python3 -m scistag.addons remove [ADDON_NAME,ADDON_NAME,...]
    """

    def __init__(self):
        pass

    def main(self, arguments):
        parser = argparse.ArgumentParser(
            prog="scistag",
            description="Installs or removes an optional add-on",
            usage="""
    SciStag Addon Manager
    ---------------------
        
    To install or remove an optional SciStag addon please use either the install
    or remove command and pass the addons you want to install or remove.
    Multiple addons can be comma separated.
            
    * python3 -m scistag.addons install [ADDON_NAME,ADDON_NAME,...]
    * python3 -m scistag.addons remove [ADDON_NAME,ADDON_NAME,...]
    
    Example:
    python3 -m scistag.addons install emojis.svg
    
    """)
        parser.add_argument("command", choices=["install", "remove"])
        params = parser.parse_args(arguments[:1])
        command = params.command
        method = getattr(self, command)
        method(arguments[1:])

    @staticmethod
    def get_all_addons() -> str:
        """
        Returns a string listing all available addons
        :return: A list of all addons as string
        """
        all_addons = scistag.addons.AddonManager.get_all_addons()
        result = []
        for key, addon in all_addons.items():
            result.append(
                f"* {key} - {addon[FEATURE_INFO]} "
                f"({addon[FEATURE_SIZE] / 2 ** 20:0.1f} MB)")
        return "\n".join(result)

    @staticmethod
    def get_installed_addons() -> str:
        """
        Returns a string listing all installed addons
        :return: A list of all installed addons as string
        """
        all_addons = scistag.addons.AddonManager.get_all_addons()
        result = []
        for key, addon in all_addons.items():
            if not AddonManager.get_addon_installed(key):
                continue
            result.append(
                f"* {key} - {addon[FEATURE_INFO]} "
                f"({addon[FEATURE_SIZE] / 2 ** 20:0.1f} MB)")
        return "\n".join(result)

    @classmethod
    def validate_addons(cls, addons: str):
        """
        Validates the addon list
        :param addons: The addon list as comma separated string as passed
            by the user.
        :return: The list of all valid addons. An empty list if the
            validation failed.
        """
        addons = addons.split(",")
        addons = [element.lstrip(" ") for element in addons]
        all_addons = AddonManager.get_all_addons()
        for element in addons:
            if element not in all_addons:
                print(f"Error, unknown addon {element}")
                return []
        return addons

    @classmethod
    def install(cls, arguments):
        """
        Called when an addon shall be installed
        :param arguments: The remaining arguments
        :return:
        """
        parser = argparse.ArgumentParser(
            prog="scistag",
            description="Installs an addon",
            usage=f"""\n
* python3 -m scistag.addons install [ADDON_NAME,ADDON_NAME,...]

List of available addons:
{cls.get_all_addons()}
        """)
        parser.add_argument("addons",
                            choices=AddonManager.get_all_addons().keys())
        params = parser.parse_args(arguments)
        addons = cls.validate_addons(params.addons)
        if len(addons) == 0:
            sys.exit(1)
        # Install all selected addons
        for element in addons:
            AddonManager.install_addon(element, verbose_if_installed=False)

    @classmethod
    def remove(cls, arguments):
        """
        Called when an addon shall be installed
        :param arguments: The remaining arguments
        :return:
        """
        parser = argparse.ArgumentParser(
            prog="scistag",
            description="Removes an addon",
            usage=f"""        
* python3 -m scistag.addons remove [ADDON_NAME,ADDON_NAME,...]

List of installed addons:
{cls.get_installed_addons()}
        """)
        parser.add_argument("addons",
                            choices=AddonManager.get_installed_addons().keys())
        params = parser.parse_args(arguments)
        addons = cls.validate_addons(params.addons)
        if len(addons) == 0:
            sys.exit(1)
        # Install all selected addons
        for element in addons:
            AddonManager.remove_addon(element)


if __name__ == '__main__':
    addon_cli = AddonCli()
    addon_cli.main(sys.argv[1:])
