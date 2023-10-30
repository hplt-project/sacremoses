from setuptools import setup

console_scripts = """
[console_scripts]
sacremoses=sacremoses.cli:cli
"""

setup(
  name = 'sacremoses',
  packages = ['sacremoses'],
  version = '0.1.0',
  description = 'SacreMoses',
  long_description = 'MosesTokenizer in Python',
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
