from scistag.vislog import LogBuilder


def main(vl: LogBuilder):
    print(f"Hello world")


LogBuilder.run(as_service=True)
