from distutils.core import setup
import setuptools

console_scripts = """
[console_scripts]
sacremoses=sacremoses.cli:cli
"""

setup(
  name = 'sacremoses',
  packages = ['sacremoses'],
  version = '0.0.35',
  description = 'SacreMoses',
  long_description = 'LGPL MosesTokenizer in Python',
  author = '',
  license = '',
  package_data={'sacremoses': ['data/perluniprops/*.txt', 'data/nonbreaking_prefixes/nonbreaking_prefix.*']},
  url = 'https://github.com/alvations/sacremoses',
  keywords = [],
  classifiers = [],
  install_requires = ['six', 'click', 'joblib', 'tqdm'],
  entry_points=console_scripts,
)
