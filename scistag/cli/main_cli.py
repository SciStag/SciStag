import argparse
import sys


class SciStagCommandLine(object):
    def __init__(self):
        parser = argparse.ArgumentParser(prog="scistag")
        # The most commonly used commands are:
        #    python3 -m scistag demo      Get an overview of all bundled demos

        subparsers = parser.add_subparsers(
            title="These are common Git commands used in various situations",
            metavar="command",
        )
        subparsers.add_parser(
            "info", help="Show info about the module and integrated plugins"
        )
        subparsers.add_parser(
            "demo", help="Execute or view the source code of a feature demo"
        )
        _ = parser.parse_args(sys.argv)

    @staticmethod
    def demo():
        from scistag.cli.cli_demo import SciStagDemoCli

        _ = SciStagDemoCli(sys.argv[2:])
