import re
import os
from setuptools import setup

console_scripts = """
[console_scripts]
sacremoses=sacremoses.cli:cli
"""

with open(os.path.join(os.path.dirname(__file__), 'sacremoses/__init__.py'), 'r') as fh:
  match = re.search(r'''^__version__\s*=\s*(["'])(.+?)\1\s*$''', fh.read(), flags=re.MULTILINE)
  assert match, "count not find __version__ in sacremoses/__init__.py"
  version = match.group(2)

with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as fh:
  long_description = fh.read()

setup(
  name = 'sacremoses',
  packages = ['sacremoses'],
  version = version,
  description = 'SacreMoses',
  long_description = long_description,
  long_description_content_type = 'text/markdown',
  author = '',
  package_data={'sacremoses': ['data/perluniprops/*.txt', 'data/nonbreaking_prefixes/nonbreaking_prefix.*']},
  url = 'https://github.com/hplt-project/sacremoses',
  keywords = [],
  classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
  ],
  install_requires = ['regex', 'click', 'joblib', 'tqdm'],
  entry_points=console_scripts,
  python_requires='>=3.8',
)