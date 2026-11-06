# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime
import re
from pathlib import Path

project = "sinklink"
author = "Ryan Kennedy"
copyright = f"{datetime.date.today().year}, the sinklink authors"

_config = (Path(__file__).parent.parent / "nextflow.config").read_text()
release = re.search(r"^\s*version\s*=\s*'([^']+)'", _config, re.M).group(1)
version = release

master_doc = "index"
source_suffix = {".md": "markdown"}

extensions = [
    "myst_parser",
    "sphinx_rtd_theme",
]
myst_enable_extensions = ["colon_fence"]
myst_heading_anchors = 3

exclude_patterns = ["_build", "README.md"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_theme_options = {"navigation_depth": 3, "collapse_navigation": False}
html_context = {
    "display_github": True,
    "github_user": "ryanjameskennedy",
    "github_repo": "sinklink",
    "github_version": "master",
    "conf_py_path": "/docs/",
}
