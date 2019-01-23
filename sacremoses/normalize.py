#!/usr/bin/env python3

"""
This is a Python port of the Moses Punctuation Normalizer from
https://github.com/moses-smt/mosesdecoder/blob/master/scripts/tokenizer/normalize-punctuation.perl
"""

import re

from typing import Callable
from typing.re import Pattern


def _substitute(string: str, pattern: str, substitution: str) -> str:
    return string.replace(pattern, substitution)

def substitute(pattern: str, substitution: str) -> Callable[[str], str]:
    return lambda x: _substitute(x, pattern, substitution)

def _substitute_regex(string: str, compiled_regex: Pattern, substitution: str):
    return compiled_regex.sub(substitution, string)

def substitute_regex(regex: str, substitution: str, ignore_case: bool = False) -> Callable[[str], str]:
    flags = re.IGNORECASE if ignore_case else 0
    compiled_regex = re.compile(regex, flags=flags)
    return lambda x: _substitute_regex(x, compiled_regex, substitution)


class MosesPunctuationNormalizer:
    """
    This is a Python port of the Moses punctuation normalizer from
    https://github.com/moses-smt/mosesdecoder/blob/master/scripts/tokenizer/normalize-punctuation.perl
    """

    SUBSTITUTIONS_EXTRA_WHITESPACE = [ # lines 21 - 30
        substitute('\r', ''),
        substitute('(', ' ('),
        substitute(')', ') '),
        substitute_regex(r' +', r' '),
        substitute_regex(r'\) ([.!:?;,])', r')\g<1>'),
        substitute('( ', '('),
        substitute(' )', ')'),
        substitute_regex(r'(\d) %', r'\g<1>%'),
        substitute(' :', ':'),
        substitute(' ;', ';'),
    ]

    SUBSTITUTIONS_NORMALIZE_UNICODE_IF_NOT_PENN = [ # lines 33 - 34
        substitute('`', "'"),
        substitute("''", ' " '),
    ]

    SUBSTITUTIONS_NORMALIZE_UNICODE = [ # lines 37 - 50
        substitute('„', '"'),
        substitute('“', '"'),
        substitute('”', '"'),
        substitute('–', '-'),
        substitute('—', ' - '),
        substitute_regex(r' +', r' '),
        substitute('´', "'"),
        substitute_regex(r'([a-z])‘([a-z])', r"\g<1>'\g<2>", ignore_case=True),
        substitute_regex(r'([a-z])’([a-z])', r"\g<1>'\g<2>", ignore_case=True),
        substitute('‘', '"'),
        substitute('‚', '"'),
        substitute('’', '"'),
        substitute("''", '"'),
        substitute("´´", '"'),
        substitute("…", "..."),
    ]

    SUBSTITUTIONS_FRENCH_QUOTES = [ # lines 52 - 57
        substitute(' « ', '"'),
        substitute('« ', '"'),
        substitute('«', '"'),
        substitute(' » ', '"'),
        substitute(' »', '"'),
        substitute('»', '"'),
    ]

    SUBSTITUTIONS_HANDLE_PSEUDO_SPACES = [ # lines 59 - 67
        substitute(' %', '%'),
        substitute('nº ', 'nº '),
        substitute(' :', ':'),
        substitute(' ºC', ' ºC'),
        substitute(' cm', ' cm'),
        substitute(' ?', '?'),
        substitute(' !', '!'),
        substitute(' ;', ';'),
        substitute(', ', ','),
        substitute_regex(r' +', r' '),
    ]

    SUBSTITUTIONS_EN_QUOTATION_FOLLOWED_BY_COMMA = [
        substitute_regex(r'"([,.]+)', r'\g<1>"'),
    ]

    SUBSTITUTIONS_DE_ES_FR_QUOTATION_FOLLOWED_BY_COMMA = [
        substitute(',"', '",'),
        substitute_regex(r'(\.+)"(\s*[^<])', r'"\g<1>\g<2>'), # don't fix period at end of sentence
    ]

    SUBSTITUTIONS_DE_ES_CZ_CS_FR = [
        substitute_regex(r'(\d) (\d)', r'\g<1>,\g<2>'),
    ]

    SUBSTITUTIONS_OTHER = [
        substitute_regex(r'(\d) (\d)', r'\g<1>.\g<2>'),
    ]

    def __init__(self, language: str = 'en', penn: bool = False):
        """
        Python port of the Moses Perl script for normalization of punctuation.

        :param language: The two-letter language code.
        :param penn: Use Penn Treebank style normalization.
        """
        self.language = language
        self.penn = penn
        # assemble sequence of substitutions
        self.substitutions = self.SUBSTITUTIONS_EXTRA_WHITESPACE
        if not self.penn:
            self.substitutions += self.SUBSTITUTIONS_NORMALIZE_UNICODE_IF_NOT_PENN
        self.substitutions += self.SUBSTITUTIONS_NORMALIZE_UNICODE
        self.substitutions += self.SUBSTITUTIONS_FRENCH_QUOTES
        self.substitutions += self.SUBSTITUTIONS_HANDLE_PSEUDO_SPACES
        if self.language == 'en':
            self.substitutions += self.SUBSTITUTIONS_EN_QUOTATION_FOLLOWED_BY_COMMA
        else:
            self.substitutions += self.SUBSTITUTIONS_DE_ES_FR_QUOTATION_FOLLOWED_BY_COMMA
        if self.language in ['de', 'es', 'cz', 'cs', 'fr']:
            self.substitutions += self.SUBSTITUTIONS_DE_ES_CZ_CS_FR
        else:
            self.substitutions += self.SUBSTITUTIONS_OTHER

    def normalize(self, string: str):
        """
        Returns a string with normalized punctuation.
        """
        for sub in self.substitutions:
            string = sub(string)
        return string
