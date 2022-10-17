"""
A simple demo showing how to use videos in SciStag
"""
import tkinter
from PIL import ImageTk
import os
from scistag.webstag import web_fetch
from scistag.mediastag import VideoSourceMovie
from scistag.common.test_data import TestConstants

video: VideoSourceMovie
last_timestamp: float = 0.0
label: tkinter.Label


def update_frame():
    """
    Get the latest frame and convert into Image
    """
    global last_timestamp, video, label
    last_timestamp, image = video.get_image(last_timestamp)
    if image is not None:
        label.camera_image = ImageTk.PhotoImage(image=image.to_pil())
        label.configure(image=label.camera_image)
    label.after(20, update_frame)


def download_video() -> str:
    """
    Downloads a demo video and returns it's local filename
    :return: The video filename
    """
    # Download the demo video
    print(f"Downloading demo video from {TestConstants.CHROME_FUN_VIDEO}...",
          end="")
    os.makedirs("temp", exist_ok=True)
    local_filename = "temp/demo_video.mp4"
    web_fetch(TestConstants.CHROME_FUN_VIDEO, filename=local_filename,
              max_cache_age=60 * 60 * 24 * 7)
    print("done")
    return local_filename


def main():
    global video
    global label
    # Download video
    video_filename = download_video()
    # Create window and label
    root = tkinter.Tk()
    root.title("A simple demo showing how to use videos in SciStag")
    label = tkinter.Label(root)
    label.grid(row=0, column=0)
    # Use camera 0. Change by your needs. You can also provide a gstreamer pipeline definition.
    video = VideoSourceMovie(filename=video_filename)
    video.start()

    update_frame()
    root.mainloop()


if __name__ == "__main__":
    main()
