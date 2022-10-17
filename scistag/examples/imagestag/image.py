"""
Simple demo which loads an image from the web using WebStag, loads it via
ImageStag and displays it in a TKInter window.
"""

import tkinter
from PIL import ImageTk

from scistag.imagestag import Image
from scistag.tests import TestConstants
from scistag.webstag import web_fetch


def main():
    root = tkinter.Tk()
    # fetch data from web
    url = TestConstants.STAG_URL
    print(f"Loading image from {url}...")
    image_data = web_fetch(url)
    # create an image
    image = Image(image_data)
    # display it
    img = ImageTk.PhotoImage(image.to_pil())
    panel = tkinter.Label(root, image=img)
    panel.pack(side="bottom", fill="both", expand="yes")
    # run the main loop
    root.mainloop()


if __name__ == "__main__":
    main()
