import os.path

from scistag.filestag import FileSource
from scistag.jupystag import Notebook


def test_clear():
    """
    Clears all example notebooks to prevent committing binary garbage to git
    """
    example_dir = os.path.dirname(__file__) + "/../../examples/"
    notebook_list = FileSource.from_source(example_dir, search_mask="*.ipynb",
                                           dont_load=True)
    for element in notebook_list:
        if "_cleaned." in element.filename:
            continue
        cur_path = notebook_list.search_path + "/" + element.filename
        notebook = Notebook(source=cur_path)
        notebook.clean()
        out_path = notebook_list.search_path + "/" + element.filename
        out_path = out_path
        notebook.save(out_path)
