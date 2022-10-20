"""
A simple demo showing how to access the camera in SciStag
"""

from tkinter import Label, Tk
from PIL import ImageTk
from scistag.mediastag.camera_cv2 import CameraCv2

# Timestamp of last received image
last_timestamp = 0.0


def update_frame():
    # Get the latest frame and convert into Image
    global last_timestamp, label
    last_timestamp, image = camera.get_image(last_timestamp)
    if image is not None:
        label.camera_image = ImageTk.PhotoImage(image=image.to_pil())
        label.configure(image=label.camera_image)
    label.after(20, update_frame)


def main():
    # Create window and label
    root = Tk()
    root.title("Example for using the camera via OpenCV")
    label = Label(root)
    label.grid(row=0, column=0)
    # Use camera 0. Change by your needs.
    # You can also provide a gstreamer pipeline definition.
    camera = CameraCv2(source=0)
    camera.start()
    update_frame()
    root.mainloop()


if __name__ == "__main__":
    main()
