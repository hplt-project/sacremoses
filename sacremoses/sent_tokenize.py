#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

from six import text_type

from sacremoses.corpus import Perluniprops
from sacremoses.corpus import NonbreakingPrefixes
from sacremoses.util import is_cjk

perluniprops = Perluniprops()
nonbreaking_prefixes = NonbreakingPrefixes()


class MosesSentTokenizer(object):
    """
    This is a Python port of the Moses Tokenizer from
    https://github.com/moses-smt/mosesdecoder/blob/master/scripts/ems/support/split-sentences.perl
    """
