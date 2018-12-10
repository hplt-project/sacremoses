#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

from collections import defaultdict, Counter
from six import text_type

from sacremoses.corpus import Perluniprops
from sacremoses.corpus import NonbreakingPrefixes

perluniprops = Perluniprops()


class MosesTruecaser(object):
    """
    This is a Python port of the Moses Truecaser from
    https://github.com/moses-smt/mosesdecoder/blob/master/scripts/recaser/train-truecaser.perl
    https://github.com/moses-smt/mosesdecoder/blob/master/scripts/recaser/truecase.perl
    """
    # Perl Unicode Properties character sets.
    Lowercase_Letter = text_type(''.join(perluniprops.chars('Lowercase_Letter')))
    Uppercase_Letter = text_type(''.join(perluniprops.chars('Uppercase_Letter')))
    Titlecase_Letter = text_type(''.join(perluniprops.chars('Uppercase_Letter')))

    def __init__(self):
        # Initialize the object.
        super(MosesTruecaser, self).__init__()
        # Initialize the language specific nonbreaking prefixes.
        self.SKIP_LETTERS_REGEX = r"[{}{}{}]".format(Lowercase_Letter,
                                    Uppercase_Letter, Titlecase_Letter)

        self.SENT_END = [".", ":", "?", "!"]
        self.DELAYED_SENT_START = ["(", "[", "\"", "'", "&apos;", "&quot;", "&#91;", "&#93;"]

    def train(self, filename, possibly_use_first_token=False):
        casing = defaultdict(Counter)
        with open(filename) as fin:
            for line in fin:
                # Keep track of first words in the sentence(s) of the line.
                is_first_word = True
                for i, token in enumerate(line.split()):
                    # Skip XML tags.
                    if re.search(r"(<\S[^>]*>)", token):
                        continue
                    # Skip if sentence start symbols.
                    elif token in self.DELAYED_SENT_START:
                        continue

                    # Resets the `is_first_word` after seeing sent end symbols.
                    if not is_first_word and token in self.SENT_END:
                        is_first_word = True
                        continue

                    # Skips words with nothing to case.
                    if not re.search(r"[{}]".format(ll_lu_lt), token):
                        is_first_word = False
                        continue

                    current_word_weight = 0
                    if not is_first_word:
                        current_word_weight = 1
                    elif possibly_use_first_token:
                        # Gated special handling of first word of sentence.
                        # Check if first characer of token is lowercase.
                        if token[0].is_lower():
                            current_word_weight = 1
                        elif i == 1:
                            current_word_weight = 0.1

                    if current_word_weight > 0:
                        casing[token.lower()][token] += current_word_weight

                    is_first_word = False
        return casing
