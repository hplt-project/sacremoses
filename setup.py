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
  # No package_data: the Unicode character classes and nonbreaking prefixes are
  # now ordinary Python modules (_data_perluniprops.py, _data_nonbreaking_prefixes.py),
  # generated from sacremoses/data/ by tools/generate_data_modules.py. The .txt
  # files stay in git as the generator's source and for the drift guard, but
  # shipping them would duplicate ~470 KB that nothing reads at run time.
  url = 'https://github.com/hplt-project/sacremoses',
  keywords = [],
  classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
  ],
  # Floors, not just names: an unconstrained requirement lets a resolver land
  # joblib 1.1.0 (CVE-2022-21797) or tqdm 4.66.2 (CVE-2024-34062). Neither is
  # reachable through this package's own calls, but nothing should ship a
  # dependency specification that permits a known-vulnerable version.
  install_requires = [
    'regex>=2021.8.3',
    'click>=8.0',
    'joblib>=1.2.0',   # CVE-2022-21797
    'tqdm>=4.66.3',    # CVE-2024-34062
  ],
  entry_points=console_scripts,
  python_requires='>=3.9',
)