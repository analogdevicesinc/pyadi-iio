# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import contextlib
import datetime
import os
import sys
from typing import List

sys.path.insert(0, os.path.abspath("../.."))
sys.path.append(os.path.abspath("./ext"))
sys.setrecursionlimit(1500)

import adi  # isort:skip

# -- Project information -----------------------------------------------------

repository = "pyadi-iio"
project = "Analog Devices Hardware Python Interfaces"
year_now = datetime.datetime.now().year
copyright = f"2019-{year_now}, Analog Devices, Inc"
author = "Travis Collins"

# The full version, including alpha/beta/rc tags
release = adi.__version__
version = release


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.githubpages",
    "myst_parser",
    "sphinxcontrib.mermaid",
    "adi_doctools",
    "ext_pyadi_iio",
]

needs_extensions = {"adi_doctools": "0.4.21"}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns: List[str] = []

# Configuration of sphinx.ext.coverage
coverage_show_missing_items = True
coverage_ignore_classes = ["phy"]
coverage_ignore_modules = ["test.dma_tests", "test.generics"]

# Link check configuration
linkcheck_ignore = [
    r"_static/logos.*",
    r"https://ez.analog.com.*",
    r"https://wiki.analog.com/resources/tools-software/linux-software/libiio/iio_.*",
]

# -- External docs configuration ----------------------------------------------

interref_repos = ["doctools"]

# -- Custom extensions configuration ------------------------------------------

hide_collapsible_content = True

# -- Options for PDF output --------------------------------------------------
if os.path.exists(os.path.join("_themes", "pdf_theme")):
    extensions.append("sphinx_simplepdf")
    html_theme_path = ["_themes"]
    simplepdf_theme = "pdf_theme"

# -- Options for HTML output -------------------------------------------------

html_theme = "cosmic"
html_favicon = os.path.join("_static", "favicon.png")

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_css_files = [
    "css/style.css",
]

html_theme_options = {
    "light_logo": os.path.join("logos", "PyADI-IIO_Logo_300_cropped.png"),
    "dark_logo": os.path.join("logos", "PyADI-IIO_Logo_w_300_cropped.png"),
}
