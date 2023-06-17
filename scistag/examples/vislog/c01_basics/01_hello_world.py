"""
This is a basic hello world demo which will add a title and a simple image from
Wikipedia to a log and host the site via a built-in server.

Steps:
* Start the application
* Click the URL http://127.0.0.1:8010/live in your console/terminal output to open the
  page in the browser of your choice. SciStag is optimized for Chrome.
* Optional: Move the browser window to your second monitor

Advanced tip for users of PyCharm for a side by side view:

* Right-click the URL in the console -> Copy URL
* Press Ctrl-Shift-A or press shift two times in a row and type "Open source..." ->
  Click on "Open Source Code from URL"
* Paste the URL and confirm. A source code tab with live will open.
* Click the little PyCharm logo in the upper right corner of the source code.
* The page will open now directly inside PyCharm and auto-reload on all changes.
* You can close the tab with the HTML code now, the website will stay open.
"""
from scistag.vislog import LogBuilder

IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/7/7f/Rotating_earth_animated_transparent.gif"


def main(vl: LogBuilder):
    """
    Main entry point
    :param vl: The LogBuilder object containing all methods to add text, images etc.
    """
    # center the content of the context:
    with vl.align.center:
        # add a title
        vl.title(f"Hello world!")
        # add an image from Wikipedia
        vl.image(IMAGE_URL, alt="planet earth")


if __name__ == "__main__":
    # Run the LogBuilder on the local file
    # def main(vl) is the default VisualLog entry point if no builder is defined
    #
    # For cleaner structuring you can flag further methods using the @cell decorator
    # to also execute these methods.
    LogBuilder.run(as_service=True)
