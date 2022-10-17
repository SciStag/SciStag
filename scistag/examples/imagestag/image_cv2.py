"""
Simple demo which loads an image from the web using WebStag, loads it via
ImageStag and displays it in a TKInter window. In addition it applies a
classic OpenCv2 filter
"""

from tkinter import Tk, Label
from PIL import ImageTk
from scistag.imagestag import Image, PixelFormat, cv
from scistag.webstag import web_fetch
from scistag.tests import TestConstants


def main():
    root = Tk()
    root.title("ImageStag + WebStag demo")
    # fetch image from the web
    image = Image(web_fetch(TestConstants.STAG_URL))
    # the original image
    img = ImageTk.PhotoImage(image.to_pil())
    panel = Label(root, image=img)
    panel.pack(side="top", fill="both", expand="yes")
    # convert image to gray scale and show it
    gray_scale = Image(cv.cvtColor(image.get_pixels(desired_format=PixelFormat.BGR), cv.COLOR_BGR2GRAY))
    img2 = ImageTk.PhotoImage(gray_scale.to_pil())
    panel = Label(root, image=img2)
    panel.pack(side="top", fill="both", expand="yes")
    # the gray scale image
    root.mainloop()


if __name__ == "__main__":
    main()
