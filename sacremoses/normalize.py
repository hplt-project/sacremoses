#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

from six import text_type


class MosesPunctNormalizer:
    """
    This is a Python port of the Moses punctuation normalizer from
    https://github.com/moses-smt/mosesdecoder/blob/master/scripts/tokenizer/normalize-punctuation.perl
    """
    EXTRA_WHITESPACE = [ # lines 21 - 30
        (r'\r', r''),
        (r'\(', r' ('),
        (r'\)', r') '),
        (r' +', r' '),
        (r'\) ([.!:?;,])', r')\g<1>'),
        (r'\( ', r'('),
        (r' \)', r')'),
        (r'(\d) %', r'\g<1>%'),
        (r' :', r':'),
        (r' ;', r';'),
    ]

    NORMALIZE_UNICODE_IF_NOT_PENN = [ # lines 33 - 34
        (r'`', r"'"),
        (r"''", r' " '),
    ]

    NORMALIZE_UNICODE = [ # lines 37 - 50
        (u'„', r'"'),
        (u'“', r'"'),
        (u'”', r'"'),
        (u'–', r'-'),
        (u'—', r' - '),
        (r' +', r' '),
        (u'´', r"'"),
    ]

    FRENCH_QUOTES = [ # lines 52 - 57
        (u' « ', r'"'),
        (u'« ', r'"'),
        (u'«', r'"'),
        (u' » ', r'"'),
        (u' »', r'"'),
        (u'»', r'"'),
    ]

    HANDLE_PSEUDO_SPACES = [ # lines 59 - 67
        (r' %', r'%'),
        (u'nº ', u'nº '),
        (r' :', r':'),
        (u' ºC', u' ºC'),
        (r' cm', r' cm'),
        (r' \?', r'\?'),
        (r' \!', r'\!'),
        (r' ;', r';'),
        (r', ', r', '),
        (r' +', r' '),
    ]

    EN_QUOTATION_FOLLOWED_BY_COMMA = [
        (r'"([,.]+)', r'\g<1>"'),
    ]

    DE_ES_FR_QUOTATION_FOLLOWED_BY_COMMA = [
        (r',"', r'",'),
        (r'(\.+)"(\s*[^<])', r'"\g<1>\g<2>'), # don't fix period at end of sentence
    ]

    DE_ES_CZ_CS_FR = [
        (r'(\d) (\d)', r'\g<1>,\g<2>'),
    ]

    OTHER = [
        (r'(\d) (\d)', r'\g<1>.\g<2>'),
    ]

    def __init__(self, lang='en', penn=False,
                 norm_quote_commas=True,
                 norm_numbers=False):
        """
        :param language: The two-letter language code.
        :type lang: str
        :param penn: Keep Penn Treebank style quotations.
        :type penn: bool
        :param norm_quote: Keep Penn Treebank style quotations.
        :type norm_quote: bool
        """
        self.substitutions = self.EXTRA_WHITESPACE

        if not penn:
            self.substitutions += self.NORMALIZE_UNICODE_IF_NOT_PENN
        self.substitutions += self.NORMALIZE_UNICODE
        self.substitutions += self.FRENCH_QUOTES
        self.substitutions += self.HANDLE_PSEUDO_SPACES

        if norm_quote_commas:
            if lang == 'en':
                self.substitutions += self.EN_QUOTATION_FOLLOWED_BY_COMMA
            elif lang in ['de', 'es', 'fr']:
                self.substitutions += self.DE_ES_FR_QUOTATION_FOLLOWED_BY_COMMA

        if norm_numbers:
            if lang in ['de', 'es', 'cz', 'cs', 'fr']:
                self.substitutions += self.DE_ES_CZ_CS_FR
            else:
                self.substitutions += self.OTHER

    def normalize(self, text):
        """
        Returns a string with normalized punctuation.
        """
        for regexp, substitution in self.substitutions:
            text = re.sub(regexp, substitution, text)
        return text
