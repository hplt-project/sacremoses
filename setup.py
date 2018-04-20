from distutils.core import setup

setup(
  name = 'sacremoses',
  packages = ['sacremoses'],
  version = '0.1.15',
  description = 'SacreMoses',
  author = '',
  license = '',
  package_data={'sacremoses': ['data/perluniprops/*.txt', 'data/nonbreaking_prefixes/nonbreaking_prefix.*']},
  url = 'https://github.com/alvations/sacremoses',
  keywords = [],
  classifiers = [],
)
