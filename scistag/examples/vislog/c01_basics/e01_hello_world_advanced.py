"""
In this second stage of the hello world demo we show you how to build more complex
logs with separated cells. Cells are (if they are not constrained with dependencies)
executed in the order they are declared within a file or class from top to bottom.

Next to a cleaner organization of your document parts cells can be refreshed, e.g. for
dynamic updating or can keep track of embedded content such as markdown files and
mermaid files to reload them when they changed on disks. But more about this later.

In addition we instead of hosting a web server we now configure the VisualLog.
Instead of a hosted version (the default) we now configure the log for "disk" logging
so everything will be stored in the subdirectory named logs, by default with
html as output format.

Advanced tip for users of PyCharm for a side by side view:
- Open the folder logs in the project overview
- Open In -> Browser -> Built-In Preview
"""

from scistag.vislog import VisualLog, cell, LogBuilder


@cell
def hello_world(vl: LogBuilder):
    with vl.align.center:  # center the content
        # Add title
        vl.title("Hello world!")
        # SciStag comes with embedded emojis. We can search for them with an asteriks
        # by their unicode standard name or use colons and their GitHub name.
        vl.emoji("*globe*", size=600).br()


@cell
def second_method(vl: LogBuilder):
    with vl.align.left:  # left-align the content
        vl.sub("How")
    with vl.align.center:  # center the content
        vl.sub("are you")
    with vl.align.right:  # right-align the content
        vl.sub("doing?")


if VisualLog.is_main():  # equals __name__=="__main__ but also works for auto-reloading
    # setup default options for disk logging and the title
    # by default only html will be exported
    options = VisualLog.setup_options("disk", title="First VisualLog")
    # create the log with the options we just set
    vl = VisualLog(options=options)
    # Run the log. if we do not provide a builder (like in the next step) the calling
    # file is scanned for all methods flagged with @cell and a method "main" with
    # a parameter vl.
    vl.run()
    # Log the url to the terminal so the user can click it
    print(f"\nThe result output is located here: {vl.local_static_url}")
