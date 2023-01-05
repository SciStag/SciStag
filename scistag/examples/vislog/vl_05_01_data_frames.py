import io
import time

from scistag.filestag import FileStag
from scistag.vislog import VisualLog, cell, LogBuilder
import pandas as pd


@cell(interval_s=0.05, continuous=True)
def say_hello():
    vl = LogBuilder.current()
    vl.title(f"Hello world").sub("How are you doing? Isn't this awesome?")
    vl.log(f"{time.time()}")
    url = "https://raw.githubusercontent.com/selva86/datasets/master/BostonHousing.csv"
    df = pd.read_csv(FileStag.load(url, as_stream=True))
    df = df.drop(columns=['crim', 'zn'])

    with vl.time.measure(prefix="Execution time: "):
        vl.pd.show(df)


if VisualLog.is_main():
    VisualLog(auto_reload=True)
