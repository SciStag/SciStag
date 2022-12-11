import os

ESSENTIAL_DATA_URL = "https://github.com/SciStag/SciStagEssentialData/releases/download/v0.0.2/scistag_essentials_0_0_2.zip"
"Url from which the essential data archive can be downloaded"
ESSENTIAL_DATA_MD5 = "e5c1e56f91c23101ba002d481bebd663"
ESSENTIAL_DATA_SIZE = 13754681

ESSENTIAL_DATA_ARCHIVE_NAME = os.path.normpath(
    os.path.dirname(__file__) + "/../data/scistag_essentials.zip"
)
"Local file name of essential data"
