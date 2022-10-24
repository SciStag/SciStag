import numpy as np

from auto_reloading import VisualLogAutoReloader
from scistag.logstag import VisualLog
from scistag.plotstag import MPLock

if __name__ == "__main__" or VisualLogAutoReloader.is_main():
    vl = VisualLog(log_to_disk=False)
    vl.text("Really wonderful!")
    vl.title("Yahooooooo!!!!!!!!")

    with MPLock() as plt:
        figure = plt.figure(figsize=(4, 4))
        plt.title("A grid with random colors, yay")
        data = np.random.default_rng().uniform(0, 1.0, (16, 16, 3))
        plt.imshow(data)
        vl.figure(figure, "random figure using MPLock")

    vl.text("This is reallly REALLY REALLY cool")

    VisualLogAutoReloader.start(vl)
