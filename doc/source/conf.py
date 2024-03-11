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
import shutil
import sys
from typing import List

sys.path.insert(0, os.path.abspath("../.."))
sys.setrecursionlimit(1500)

# Move logos over to doc directory
p = os.path.join("_static", "logos")
if not os.path.exists(p):
    os.mkdir("_static/logos")

for filename in os.listdir(os.path.join("..", "..", "images")):
    if filename.endswith(".png"):
        shutil.copy(
            os.path.join("..", "..", "images", filename),
            os.path.join("_static", "logos", filename),
        )
        fn = os.path.join("_static", "logos", filename)
        from PIL import Image

        im = Image.open(fn)
        # Remove left 30% of image
        im = im.crop((int(im.size[0] * 0.45), 0, int(im.size[0] * 1), im.size[1]))
        im.save(fn.replace(".png", "_cropped.png"))


import adi  # isort:skip

# -- Project information -----------------------------------------------------

project = "pyadi-iio"
year_now = datetime.datetime.now().year
copyright = f"2019-{year_now}, Analog Devices, Inc"
author = "Travis Collins"

# The full version, including alpha/beta/rc tags
release = adi.__version__
version = release


# -- General configuration ---------------------------------------------------

# The master toctree document.
master_doc = "index"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.githubpages",
    "myst_parser",
    # "sphinx_favicon",
    "sphinxcontrib.mermaid",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.wavedrom",
    "adi_doctools",
]


needs_extensions = {"adi_doctools": "0.3"}

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

# -- External docs configuration ----------------------------------------------

intersphinx_mapping = {
    "doctools": ("https://analogdevicesinc.github.io/doctools", None)
}

# -- Custom extensions configuration ------------------------------------------

hide_collapsible_content = True
validate_links = False

# -- Options for PDF output --------------------------------------------------
if os.path.exists(os.path.join("_themes", "pdf_theme")):
    extensions.append("sphinx_simplepdf")
    html_theme_path = ["_themes"]
    simplepdf_theme = "pdf_theme"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "cosmic"

html_title = f"{project} {release}"
# favicons = ["favicon.png"]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# html_css_files = [
#     "css/style.css",
# ]

# html_theme_options = {
#     "light_logo": os.path.join("logos", "PyADI-IIO_Logo_300_cropped.png"),
#     "dark_logo": os.path.join("logos", "PyADI-IIO_Logo_w_300_cropped.png"),
#     "dark_css_variables": {
#         "color-sidebar-item-background--current": "white",
#         "color-sidebar-link-text": "white",
#         "color-sidebar-link-text--top-level": "white",
#     },
#     "light_css_variables": {
#         "color-sidebar-item-background--current": "black",
#         "color-sidebar-link-text": "black",
#         "color-sidebar-link-text--top-level": "black",
#     },
# }

if os.getenv("DEV_BUILD"):
    branch = os.getenv("GIT_BRANCH")
    if branch is None:
        with contextlib.suppress(Exception):
            # Try to get branch from git
            import subprocess

            branch = (
                subprocess.run(
                    args=["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                )
                .stdout.decode("utf-8")
                .strip()
            )
    if branch is None:
        branch = "_UNKNOWN_"  # type: ignore
    html_theme_options["announcement"] = (
        "<em>WARNING: This is a development \
        build of branch: <b>"
        + branch
        + "</b>. Please use the latest stable release.</em>"
    )
    html_theme_options["dark_css_variables"]["color-announcement-text"] = "red"
    html_theme_options["light_css_variables"]["color-announcement-text"] = "red"
