import ntpath
import os
import sys

module_path = os.path.normpath(os.path.dirname(__file__) + "/../../")
print(f"Adding module path {module_path}...", flush=True)
sys.path.append(module_path)
sys.path.append(os.path.dirname(__file__))
from custom_generator import generate

generate()
import scistag
import sphinx_rtd_theme

# -- General configuration -----------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.doctest",
    "sphinx_mdinclude",
    "sphinx.ext.autosummary",  # Create neat summary tables for modules/classes/methods etc
    "sphinx_autodoc_typehints",  # Automatically document param types (less noise in class signature)
]

source_suffix = ".rst"
master_doc = "index"
author = "Michael Ikemann"

# General information about the project.
project = "SciStag"
copyright = "2022, Michael Ikemann"

version = scistag.__version__
release = version

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

pygments_style = "sphinx"

autosummary_generate = True  # Turn on sphinx.ext.autosummary
autoclass_content = "both"
autodoc_mock_imports = ["kivy"]
autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
add_module_names = False  # Remove namespaces from class/method signatures

# -- Options for HTML output ---------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ["_static"]

# -- Extensions ----------------------------------------------------------------

autodoc_member_order = "groupwise"

intersphinx_mapping = {
    "http://docs.python.org/": None,
}


def autodoc_skip_member_callback(app, what, name, obj, skip, options):
    exclude = False
    return skip or exclude


# ----- skip  docstring in module for test case-----------------------------


def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip_member_callback)
    app.add_css_file("theme_customizing.css")
