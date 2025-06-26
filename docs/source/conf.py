import os
import sys

sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------
project = 'DenoiseBuddyBot'
copyright = '2025, Mozzhukhin A., Efremova I., Nikitin M., Gaidei M.'
author = 'Mozzhukhin A., Efremova I., Nikitin M., Gaidei M.'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autodoc.typehints',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

autodoc_typehints = "signature"

# "Мокаем" cupy, чтобы сборка не зависела от его наличия
autodoc_mock_imports = ['cupy']


templates_path = ['_templates']
exclude_patterns = []
language = 'ru'

# -- Options for HTML output -------------------------------------------------
html_theme = 'furo'
html_static_path = ['_static']

# -- Intersphinx configuration -----------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'cupy': ('https://docs.cupy.dev/en/stable/', os.path.join(os.path.dirname(__file__), '_inv/cupy_objects.inv'))
}