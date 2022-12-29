"""
This demo shows VisualLogStag's auto-reload capability and some basic features.

For further instructions see the method build_body below
"""

from math import ceil

import numpy as np
import pandas as pd

from scistag.vislog import VisualLog, LogBuilder
from scistag.emojistag import EmojiDb, render_emoji


class DemoBuilder(LogBuilder):
    def build(self):
        self.md(
            """
            # Welcome to SciStag VisualLog!
            
            ## About
            
            VisualLog is a dynamic logging solution with a **built-in HTML
            and markdown** writer and a webserver based upon **Flask** - and 
            **FastAPI** alternatively in the future.
            
            It is optimized for the easier development of data science and
            data engineering solutions as the internal server reflects every
            (saved) change to the source code asap in the browser view
            thus giving you very fast feedback which impact the change of
            your SQL query or hyperparameter has on your solution.
            
            ## Getting started
            
            * Install SciStag with Flask installed, e.g. via 
            `pip install scistag[logstag,flask]`
            * Start this demo in the IDE of your choice such as Visual Studio
            Code or PyCharm Professional.
            * After starting the demo you should see an 
            url such as [http://127.0.0.1:8010/live](http://127.0.0.1:8010/live) 
            in your log.
                * Copy this URL to the clipboard, it has to be the one ending
                with /live
            * Afterwards either open this URL in your browser and show it side 
            by side next to your source code 
            
            **PyCharm Professional**:
            
            * Just right-click on the URL in the console and click **Copy URL**
            * Press **Ctrl-Shift-A**
                * Type ***Open Source Code from URL***
                * Enter the just pasted URL and confirm
                * Take care of trailing white spaces ;-) 
            * In the new editor pane click the small PyCharm icon in the upper 
              right corner of the editor pane to show the embedded browser. 
            * Afterwards you can close the tab showing the html source code, the 
              browser will stay independent of that and you can now live edit 
              your logs.
              
            Now you should be able to see this guide in the browser you chose.                          
            
            ## Magic!
            * So far, so well, but when ever you now edit something, add
            a new matplot plot, insert an image, a dataframe or what ever
            you like and save the file again, e.g. via **Ctrl-S** these changes 
            will  asap reflect in the browser, hopefully saving you a lot of 
            time re-starting your code over and over again.
            * This reload mechanism actually works so evil fast that you can 
            even easily update the content of a FullHD video live stream at 
            60 fps on a modern PC and update this live in the browser, see the
            live_camera.py demo next to this one.
            
            **Note:** **SciStag** is still in a very early alpha phase.
              
            **Have fun**!"""
        )
        self.image(render_emoji(":sunglasses:", height=64))
        self.hr()
        self.show_dataframe()
        self.hr()
        self.show_images()
        self.hr()
        self.show_plots()

    def show_dataframe(self):
        """
        Demo showing how to add a dataframe to your log
        :return:
        """
        self.sub("Adding Pandas data frames to your log")
        d = {
            "one": pd.Series([10, 20, 30, 40], index=["a", "b", "c", "d"]),
            "two": pd.Series([10, 20, 30, 40], index=["a", "b", "c", "d"]),
        }
        df = pd.DataFrame(d)
        self.add(df)

    def show_images(self):
        """
        Demo showing how to add tables and images to a log
        """
        self.sub("Adding images from the web to your log")
        self.image(
            "https://github.com/SciStag/SciStagEssentialData/releases/download/v0.0.2/stag.jpg"
        )
        self.sub("Adding dynamic created images to your log")
        emojis = EmojiDb.find_emojis_by_name("*smiling*")
        valid_emojis = [emoji.image for emoji in emojis if emoji.image is not None]
        per_row = 4
        rows = int(ceil(len(valid_emojis) / per_row))
        table = self.table.begin()
        for cur_row in range(rows):
            content = valid_emojis[cur_row * per_row : cur_row * per_row + per_row]
            table.add_row(content)
        table.close()

    def show_plots(self):
        """
        Demo showing how to add matplotlib figures to your log
        """
        self.sub("Matplot Demo")
        with self.pyplot() as plt:
            fig, (ax1, ax2) = plt.subplots(2, 1)
            # make a little extra space between the subplots
            fig.subplots_adjust(hspace=0.5)
            dt = 0.01
            t = np.arange(0, 30, dt)
            # Fixing random state for reproducibility
            np.random.seed(19680801)
            nse1 = np.random.randn(len(t))  # white noise 1
            nse2 = np.random.randn(len(t))  # white noise 2
            r = np.exp(-t / 0.05)
            cnse1 = np.convolve(nse1, r, mode="same") * dt  # colored noise 1
            cnse2 = np.convolve(nse2, r, mode="same") * dt  # colored noise 2
            # two signals with a coherent part and a random part
            s1 = 0.01 * np.sin(2 * np.pi * 10 * t) + cnse1
            s2 = 0.01 * np.sin(2 * np.pi * 10 * t) + cnse2
            ax1.plot(t, s1, t, s2)
            ax1.set_xlim(0, 5)
            ax1.set_xlabel("Time")
            ax1.set_ylabel("s1 and s2")
            ax1.grid(True)
            cxy, f = ax2.csd(s1, s2, 256, 1.0 / dt)
            ax2.set_ylabel("CSD (dB)")


if VisualLog.is_main():
    VisualLog(auto_reload=DemoBuilder)  # No archived files needed
