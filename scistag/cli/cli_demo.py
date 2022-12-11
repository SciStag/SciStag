import argparse


class SciStagDemoCli:
    def __init__(self, parameters):
        parser = argparse.ArgumentParser(
            description="View or execute one of SciStag's code samples"
        )
        parser.add_argument("command", action="list")
        args = parser.parse_args(parameters)
