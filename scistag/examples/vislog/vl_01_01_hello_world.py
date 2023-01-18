"""
This is a basic hello world demo which will add a title and a simple image from
Wikipedia to a log and host the site via a built-in server.

Steps:
* Start the application
* Click the URL http://127.0.0.1:8010/live in your console/terminal output to open the
  page in the browser of your choice. SciStag is optimized for Chrome.
* Move the browser window to your second monitor or use Windows Key+Cursor Left in your
  IDE window and Windows+Cursor Right in your browser window for a split view on Linux
  and Windows.
  Under OS X just click and hold the window's green maximize button and choose the
  window sides for each window.

Tip for users of PyCharm who want to see the log directly inside PyCharm:
* Right-click the URL in the console -> Copy URL
* Press Ctrl-Shift-A -> Type "Open source..." -> Click on "Open Source Code from URL"
* Paste the URL and confirm. A source code tab with live will open.
* Click the PyCharm logo in the upper right corner of the source code.
* The page will open now directly inside PyCharm and auto-reload on all changes.
* You can close the tab with the HTML code now, the website will stay open.
"""
from scistag.vislog import LogBuilder

IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/7/7f/Rotating_earth_animated_transparent.gif"


def main(vl: LogBuilder):
    with vl.align.center:
        vl.title(f"Hello world!")
        vl.image(IMAGE_URL, alt="planet earth")


LogBuilder.run(as_service=True)
