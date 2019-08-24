#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

from six import text_type
from itertools import chain


class MosesPunctNormalizer:
    """
    This is a Python port of the Moses punctuation normalizer from
    https://github.com/moses-smt/mosesdecoder/blob/master/scripts/tokenizer/normalize-punctuation.perl
    """

    EXTRA_WHITESPACE = [  # lines 21 - 30
        (r"\r", r""),
        (r"\(", r" ("),
        (r"\)", r") "),
        (r" +", r" "),
        (r"\) ([.!:?;,])", r")\g<1>"),
        (r"\( ", r"("),
        (r" \)", r")"),
        (r"(\d) %", r"\g<1>%"),
        (r" :", r":"),
        (r" ;", r";"),
    ]

    NORMALIZE_UNICODE_IF_NOT_PENN = [(r"`", r"'"), (r"''", r' " ')]  # lines 33 - 34

    NORMALIZE_UNICODE = [ # lines 37 - 50
        (u'„', r'"'),
        (u'“', r'"'),
        (u'”', r'"'),
        (u'–', r'-'),
        (u'—', r' - '),
        (r' +', r' '),
        (u'´', r"'"),
        (u'([a-zA-Z])‘([a-zA-Z])', r"\g<1>'\g<2>"),
        (u'([a-zA-Z])’([a-zA-Z])', r"\g<1>'\g<2>"),
        (u'‘', r'"'),
        (u'‚', r'"'),
        (u'’', r'"'),
        (r"''", r'"'),
        (u'´´', r'"'),
        (u'…', r'...'),
    ]

    FRENCH_QUOTES = [ # lines 52 - 57
        (u'\u00A0«\u00A0', r'"'),
        (u'«\u00A0', r'"'),
        (u'«', r'"'),
        (u'\u00A0»\u00A0', r'"'),
        (u'\u00A0»', r'"'),
        (u'»', r'"'),
    ]

    HANDLE_PSEUDO_SPACES = [ # lines 59 - 67
        (u'\u00A0%', r'%'),
        (u'nº\u00A0', u'nº '),
        (u'\u00A0:', r':'),
        (u'\u00A0ºC', u' ºC'),
        (u'\u00A0cm', r' cm'),
        (u'\u00A0\\?', u'?'),
        (u'\u00A0\\!', u'!'),
        (u'\u00A0;', r';'),
        (u',\u00A0', r', '),
        (r' +', r' '),
    ]

    EN_QUOTATION_FOLLOWED_BY_COMMA = [(r'"([,.]+)', r'\g<1>"')]

    DE_ES_FR_QUOTATION_FOLLOWED_BY_COMMA = [
        (r',"', r'",'),
        (r'(\.+)"(\s*[^<])', r'"\g<1>\g<2>'),  # don't fix period at end of sentence
    ]

    DE_ES_CZ_CS_FR = [
        (u'(\\d)\u00A0(\\d)', r'\g<1>,\g<2>'),
    ]

    OTHER = [
        (u'(\\d)\u00A0(\\d)', r'\g<1>.\g<2>'),
    ]

    def __init__(self, lang="en", penn=True, norm_quote_commas=True, norm_numbers=True):
        """
        :param language: The two-letter language code.
        :type lang: str
        :param penn: Normalize Penn Treebank style quotations.
        :type penn: bool
        :param norm_quote_commas: Normalize quotations and commas
        :type norm_quote_commas: bool
        :param norm_numbers: Normalize numbers
        :type norm_numbers: bool
        """
        self.substitutions = [
            self.EXTRA_WHITESPACE,
            self.NORMALIZE_UNICODE,
            self.FRENCH_QUOTES,
            self.HANDLE_PSEUDO_SPACES,
        ]

        if penn:  # Adds the penn substitutions after extra_whitespace regexes.
            self.substitutions.insert(1, self.NORMALIZE_UNICODE_IF_NOT_PENN)

        if norm_quote_commas:
            if lang == "en":
                self.substitutions.append(self.EN_QUOTATION_FOLLOWED_BY_COMMA)
            elif lang in ["de", "es", "fr"]:
                self.substitutions.append(self.DE_ES_FR_QUOTATION_FOLLOWED_BY_COMMA)

        if norm_numbers:
            if lang in ["de", "es", "cz", "cs", "fr"]:
                self.substitutions.append(self.DE_ES_CZ_CS_FR)
            else:
                self.substitutions.append(self.OTHER)

        self.substitutions = list(chain(*self.substitutions))

    def normalize(self, text):
        """
        Returns a string with normalized punctuation.
        """
        for regexp, substitution in self.substitutions:
            # print(regexp, substitution)
            text = re.sub(regexp, substitution, text_type(text))
            # print(text)
        return text
