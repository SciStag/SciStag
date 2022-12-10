"""
A simple demo showing how to access the camera in SciStag
"""

from tkinter import Label, Tk
from PIL import ImageTk
from scistag.mediastag.camera_cv2 import CameraCv2


class WebCamDemo:

    def __init__(self):
        self.root = Tk()
        self.root.title("Example for using the camera via OpenCV")
        self.label = Label(self.root)
        self.label.grid(row=0, column=0)
        # Use camera 0. Change by your needs.
        # You can also provide a gstreamer pipeline definition.
        self.camera = CameraCv2(source=0)
        self.last_timestamp = 0.0

    def update_frame(self):
        # Get the latest frame and convert into Image
        self.last_timestamp, image = self.camera.get_image(self.last_timestamp)
        if image is not None:
            self.label.camera_image = ImageTk.PhotoImage(image=image.to_pil())
            self.label.configure(image=self.label.camera_image)
        self.label.after(20, self.update_frame)

    def run(self):
        # Start camera
        self.camera.start()
        # Initiate label update
        self.update_frame()
        # Run Tk main loop
        self.root.mainloop()


if __name__ == "__main__":
    WebCamDemo().run()
