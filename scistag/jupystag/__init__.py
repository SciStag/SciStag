"""
Helper functions to handle Jupyter Notebooks
"""
import json

NOTEBOOK_CELL_DATA = "data"
"Data part of a cell"

NOTEBOOK_CELL_TYPE_CODE = "code"
"Cell type Code"

NOTEBOOK_CELL_TYPE_MARKDOWN = "markdown"
"Cell type Markdown"

NOTEBOOK_CELL_OUTPUTS = "outputs"
"Output part of a cell"

NOTEBOOK_CELL_TYPE = "cell_type"
"Cell's type"

NOTEBOOK_CELLS = "cells"
"The cell list"


class Notebook:
    """
    Jupyter notebook helper class.

    Is able to load a notebook, provide statistics about it and clean it,
    for example to use it in a pre-commit hook.
    """

    def __init__(self, source: str):
        """
        :param source: The notebooks filename
        """
        self.name = source
        "The origin filename"
        with open(source, "r", encoding="utf-8") as nb_file:
            self.notebook = json.load(nb_file)
            "The notebook data"
        self.cell_count = 0
        "Total cell count"
        self.mark_down_cells = 0
        "Count of markdown cells"
        self.code_cells = 0
        "Count of code cells"
        self.output_data_size = 0
        "The total size of the output data"
        self.is_dirty = True
        "Defines if the Notebook is dirty, e.g. has a counter of outputs"
        self.parse()

    def save(self, filename: str):
        """
        Saves the notebook to disk

        :param filename: The target filename
        """
        with open(filename, "w", encoding="utf-8") as nb_file:
            nb_file.write(json.dumps(self.notebook, indent=1))

    def parse(self):
        """
        Parses the notebook to receive some details about it
        """
        for cell in self.notebook.get(NOTEBOOK_CELLS, []):
            self.cell_count += 1
            cell_type = cell.get(NOTEBOOK_CELL_TYPE, "")
            if cell_type == NOTEBOOK_CELL_TYPE_MARKDOWN:
                self.mark_down_cells += 1
            elif cell.get(NOTEBOOK_CELL_TYPE, "") == NOTEBOOK_CELL_TYPE_CODE:
                self.code_cells += 1
            outputs = cell.get(NOTEBOOK_CELL_OUTPUTS, [])
            for output in outputs:
                output: dict
                total_size = 0
                if NOTEBOOK_CELL_DATA in output:
                    total_size += sum(
                        [len(value) for value in
                         output[NOTEBOOK_CELL_DATA].values()])
                self.output_data_size += total_size

    def clean(self,
              clear_outputs=True,
              clear_metadata=True,
              clear_counters=True):
        """
        Removes temporary data from the notebook such as outputs and execution
        counters.

        :param clear_outputs: Clear all outputs?
        :param clear_metadata: Clear metadata?
        :param clear_counters: Clear counters?
        """
        for cell in self.notebook.get(NOTEBOOK_CELLS, []):
            self.cell_count += 1
            cell_type = cell.get(NOTEBOOK_CELL_TYPE, "")
            if cell_type == NOTEBOOK_CELL_TYPE_MARKDOWN:
                self.mark_down_cells += 1
            elif cell.get(NOTEBOOK_CELL_TYPE, "") == NOTEBOOK_CELL_TYPE_CODE:
                self.code_cells += 1
            if NOTEBOOK_CELL_OUTPUTS in cell and clear_outputs:
                cell[NOTEBOOK_CELL_OUTPUTS] = []
            if "metadata" in cell and clear_metadata:
                cell["metadata"] = {}
            if "execution_count" in cell and clear_counters:
                cell["execution_count"] = None

    def __str__(self):
        repr_str = "Notebook"
        repr_str += f"\n* cells: {self.cell_count}"
        repr_str += f"\n    * code: {self.code_cells}"
        repr_str += f"\n    * markdown: {self.mark_down_cells}"
        repr_str += f"\n* outputSize: {self.output_data_size}"
        return repr_str
