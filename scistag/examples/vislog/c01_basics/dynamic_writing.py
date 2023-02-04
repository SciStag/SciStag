from scistag.vislog import VisualLog


class SomeClassForDataEngineering:
    def __init__(self):
        options = VisualLog.setup_options("disk")
        options.output.setup(console=True, disk=True, formats={"html", "txt"})
        self.logger = VisualLog(options)
        self.vl = self.logger.default_builder

    def process_data(self):
        self.vl.log.info("Loading data")
        self.vl.log.error("Something went wrong")

    def finalize(self):
        self.vl.log.info("Processing finished")
        self.logger.finalize()


if __name__ == "__main__":
    data_processor = SomeClassForDataEngineering()
    data_processor.process_data()
    data_processor.finalize()
    print(
        f"Processing finished, results located "
        f"at {data_processor.logger.local_static_url}"
    )
