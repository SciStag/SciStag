import os
import shutil


def duplicate_images():
    """
    Duplicates some images when building the documentation as workaround for a bug in the sphinx_md module which
    includes the images not relative to the markdown file but relative to the config.py directory.
    :return:
    """
    local_path = os.path.dirname(__file__)
    try:
        shutil.rmtree(local_path + "/docs")
    except FileNotFoundError:
        pass
    os.makedirs(local_path + "/docs/source", exist_ok=True)
    shutil.copytree("./generated", local_path + "/docs/source/generated")


def generate():
    """
    Generates dynamic pages and images for the SciStag docu
    """
    duplicate_images()
