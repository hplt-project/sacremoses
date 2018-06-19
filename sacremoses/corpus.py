#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import os

class Perluniprops:
    """
    This class is used to read lists of characters from the Perl Unicode
    Properties (see http://perldoc.perl.org/perluniprops.html).
    The files in the perluniprop.zip are extracted using the Unicode::Tussle
    module from http://search.cpan.org/~bdfoy/Unicode-Tussle-1.11/lib/Unicode/Tussle.pm
    """
    def __init__(self):
        self.datadir = os.path.dirname(os.path.abspath(__file__)) + '/data/perluniprops/'
        # These are categories similar to the Perl Unicode Properties
        self.available_categories = ['Close_Punctuation', 'Currency_Symbol',
                                     'IsAlnum', 'IsAlpha', 'IsLower', 'IsN', 'IsSc',
                                     'IsSo', 'IsUpper', 'Line_Separator', 'Number',
                                     'Open_Punctuation', 'Punctuation', 'Separator',
                                     'Symbol']

    def chars(self, category=None, fileids=None):
        """
        This module returns a list of characters from  the Perl Unicode Properties.
        They are very useful when porting Perl tokenizers to Python.

            >>> from profanebleu.corpus import perluniprops as pup
            >>> pup.chars('Open_Punctuation')[:5] == [u'(', u'[', u'{', u'\u0f3a', u'\u0f3c']
            True
            >>> pup.chars('Currency_Symbol')[:5] == [u'$', u'\xa2', u'\xa3', u'\xa4', u'\xa5']
            True
            >>> pup.available_categories
            ['Close_Punctuation', 'Currency_Symbol', 'IsAlnum', 'IsAlpha', 'IsLower', 'IsN', 'IsSc', 'IsSo', 'IsUpper', 'Line_Separator', 'Number', 'Open_Punctuation', 'Punctuation', 'Separator', 'Symbol']

        :return: a generator of characters given the specific unicode character category
        """
        with io.open(self.datadir+category+'.txt', encoding='utf8') as fin:
            for ch in fin.read().strip():
                yield ch


class NonbreakingPrefixes:
    """
    This is a class to read the nonbreaking prefixes textfiles from the
    Moses Machine Translation toolkit. These lists are used in the Python port
    of the Moses' word tokenizer.
    """
    def __init__(self):
        self.datadir = os.path.dirname(os.path.abspath(__file__)) + '/data/nonbreaking_prefixes/'
        self.available_langs = {'catalan':    'ca',
                                'czech':      'cs',
                                'german':     'de',
                                'greek':      'el',
                                'english':    'en',
                                'spanish':    'es',
                                'finnish':    'fi',
                                'french':     'fr',
                                'hungarian':  'hu',
                                'icelandic':  'is',
                                'italian':    'it',
                                'latvian':    'lv',
                                'dutch':      'nl',
                                'polish':     'pl',
                                'portuguese': 'pt',
                                'romanian':   'ro',
                                'russian':    'ru',
                                'slovak':     'sk',
                                'slovenian':  'sl',
                                'swedish':    'sv',
                                'tamil':      'ta'}
        # Also, add the lang IDs as the keys.
        self.available_langs.update({v:v for v in self.available_langs.values()})

    def words(self, lang=None, ignore_lines_startswith='#'):
        """
        This module returns a list of nonbreaking prefixes for the specified
        language(s).

            >>> from profanebleu.corpus import nonbreaking_prefixes as nbp
            >>> nbp.words('en')[:10] == [u'A', u'B', u'C', u'D', u'E', u'F', u'G', u'H', u'I', u'J']
            True
            >>> nbp.words('ta')[:5] == [u'\u0b85', u'\u0b86', u'\u0b87', u'\u0b88', u'\u0b89']
            True

        :return: a generator words for the specified language(s).
        """
        # If *lang* in list of languages available, allocate apt fileid.
        if lang in self.available_langs:
            filenames = ['nonbreaking_prefix.'+self.available_langs[lang]]
        # Use non-breaking praefixes for all languages when lang==None.
        elif lang == None:
            filenames = ['nonbreaking_prefix.'+v for v in
                         set(self.available_langs.values())]
        else:
            filenames = ['nonbreaking_prefix.en']

        for filename in filenames:
            with io.open(self.datadir+filename, encoding='utf8') as fin:
                for line in fin:
                    line = line.strip()
                    if line and not line.startswith(ignore_lines_startswith):
                        yield line
