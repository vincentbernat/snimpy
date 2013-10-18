#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os

rtd = os.environ.get('READTHEDOCS', None) == 'True'
cwd = os.getcwd()
project_root = os.path.dirname(cwd)
sys.path.insert(0, project_root)

# -- Don't try to load CFFI (doesn't work on RTD) ------------------------------

if rtd:
    from mock import Mock
    sys.modules['cffi'] = Mock()
import snimpy

# -- General configuration -----------------------------------------------------

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# General information about the project.
project = u'Snimpy'
copyright = u'2013, Vincent Bernat'

version = snimpy.__version__
release = snimpy.__version__

exclude_patterns = ['_build']
pygments_style = 'sphinx'

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
sys.path.append(os.path.abspath('_themes'))
html_theme_path = ['_themes']
html_theme = 'flask'
html_static_path = ['_static']
html_use_modindex = False
html_theme_options = {
    "index_logo": "snimpy.svg",
    "index_logo_height": "200px"
}
htmlhelp_basename = 'snimpydoc'
