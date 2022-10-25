import numpy as np

from scistag.logstag.visual_log.visual_log_autoreloader import \
    VisualLogAutoReloader
from scistag.logstag import VisualLog
from scistag.plotstag import MPLock

if __name__ == "__main__" or VisualLogAutoReloader.is_main():
    vl = VisualLog(log_to_disk=False)
    vl.text("Really wonderful!")
    vl.title("Yahoo!!!!")

    with vl.pyplot() as plt:
        plt.title("A grid with random colors, yay")
        data = np.random.default_rng().uniform(0, 1.0, (20, 28, 3))
        plt.imshow(data)

    VisualLogAutoReloader.start(vl)
