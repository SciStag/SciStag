import time

import numpy as np

from scistag.logstag.visual_log.visual_log_autoreloader import \
    VisualLogAutoReloader
from scistag.logstag import VisualLog


def test_function():
    return 123


if __name__ == "__main__" or VisualLogAutoReloader.is_main():
    vl = VisualLog(log_to_disk=False, auto_reload=True, cache_version=3)
    vl.text("Really wonderful!")
    vl.title("Yahoo!!!!!!!")

    cached_function = vl.cache.cache("someFunction", lambda: test_function)
    session_id = vl.cache.cache("./sessionId@0", lambda: time.time())

    vl.log(str(session_id))
    vl.log("Text123")
    vl.log(str(cached_function()))

    with vl.pyplot() as plt:
        plt.title("A grid with random colors, yay")
        data = vl.cache.cache("./randomData",
                              lambda: np.random.default_rng().uniform(0, 1.0, (
                                  128, 128, 3)))
        plt.imshow(data)
    VisualLogAutoReloader.start(vl)
