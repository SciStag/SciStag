"""
Simple demo which loads an image from the web and applies different filters
"""

import tkinter
from PIL import ImageTk
from scistag.imagestag import Image
from scistag.imagestag.filters import GrayscaleFilter, ColorMapFilter
from scistag.imagestag.filters.resize_filter import ResizeFilter
from scistag.tests import TestConstants


def main():
    root = tkinter.Tk()
    root.title("Example of ImageFilter, Grayscale and FalseColor")
    image = Image(TestConstants.STAG_URL).resized_ext(factor=0.5)
    # the original image
    img = ImageTk.PhotoImage(image.to_pil())
    panel = tkinter.Label(root, image=img)
    panel.pack(side="top", fill="both", expand="yes")
    # the grayscale image
    img2 = ImageTk.PhotoImage(GrayscaleFilter().filter(image).to_pil())
    panel = tkinter.Label(root, image=img2)
    panel.pack(side="top", fill="both", expand="yes")
    # the falsecolor image
    img3 = ImageTk.PhotoImage(
        ColorMapFilter(color_map="viridis").filter(image).to_pil()
    )
    panel = tkinter.Label(root, image=img3)
    panel.pack(side="top", fill="both", expand="yes")
    # a rescaled image
    img4 = ImageTk.PhotoImage(ResizeFilter(target_aspect=16 / 9).filter(image).to_pil())
    panel = tkinter.Label(root, image=img4)
    panel.pack(side="top", fill="both", expand="yes")

    root.mainloop()


if __name__ == "__main__":
    main()
