import io
import time

from scistag.filestag import FileStag
from scistag.vislog import VisualLog, cell, LogBuilder
import pandas as pd


@cell(interval_s=0.05, continuous=True)
def show_():
    vl = LogBuilder.current()
    vl.cell["say_hello"].log_statistics()
    vl.br()
    url = "https://raw.githubusercontent.com/selva86/datasets/master/BostonHousing.csv"
    df = pd.read_csv(FileStag.load(url, as_stream=True))
    df = df.drop(columns=["crim", "zn"])

    with vl.time.measure(prefix="\nExecution time: "):
        vl.pd.show(df)


if VisualLog.is_main():
    VisualLog().run_server(auto_reload=True)
