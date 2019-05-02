# -*- coding: utf-8 -*-

"""
Tests for MosesTokenizer
"""

import unittest

from sacremoses.tokenize import MosesTokenizer, MosesDetokenizer

class TestTokenzier(unittest.TestCase):
    def test_moses_tokenize(self):
        moses = MosesTokenizer()

        # Tokenize a sentence.
        text = u'This, is a sentence with weird\xbb symbols\u2026 appearing everywhere\xbf'
        expected_tokens = u'This , is a sentence with weird \xbb symbols \u2026 appearing everywhere \xbf'
        tokenized_text =  moses.tokenize(text, return_str=True)
        assert tokenized_text == expected_tokens

        # The nonbreaking prefixes should tokenize the final fullstop.
        assert moses.tokenize('abc def.') == [u'abc', u'def', u'.']

        # The nonbreaking prefixes should deal the situation when numeric only prefix is the last token.
        # In below example, "pp" is the last element, and there is no digit after it.
        assert moses.tokenize ('2016, pp.') == [u'2016', u',', u'pp', u'.']

        # Test escape_xml
        text = "This ain't funny. It's actually hillarious, yet double Ls. | [] < > [ ] & You're gonna shake it off? Don't?"
        expected_tokens_with_xmlescape = ['This', 'ain', '&apos;t', 'funny', '.', 'It', '&apos;s', 'actually', 'hillarious', ',', 'yet', 'double', 'Ls', '.', '&#124;', '&#91;', '&#93;', '&lt;', '&gt;', '&#91;', '&#93;', '&amp;', 'You', '&apos;re', 'gonna', 'shake', 'it', 'off', '?', 'Don', '&apos;t', '?']
        expected_tokens_wo_xmlescape = ['This', 'ain', "'t", 'funny', '.', 'It', "'s", 'actually', 'hillarious', ',', 'yet', 'double', 'Ls', '.', '|', '[', ']', '<', '>', '[', ']', '&', 'You', "'re", 'gonna', 'shake', 'it', 'off', '?', 'Don', "'t", '?']
        assert moses.tokenize(text, escape=True) == expected_tokens_with_xmlescape
        assert moses.tokenize(text, escape=False) == expected_tokens_wo_xmlescape

        # Test to check https://github.com/alvations/sacremoses/issues/19
        text = "this 'is' the thing"
        expected_tokens = ['this', '&apos;', 'is', '&apos;', 'the', 'thing']
        assert moses.tokenize(text, escape=True) == expected_tokens

    def test_aggressive_split(self):
        moses = MosesTokenizer()
        expected_tokens_wo_aggressive_dash_split = ['foo-bar']
        expected_tokens_with_aggressive_dash_split = ['foo', '@-@', 'bar']

        assert moses.tokenize('foo-bar') == expected_tokens_wo_aggressive_dash_split
        assert moses.tokenize('foo-bar', aggressive_dash_splits=True) == expected_tokens_with_aggressive_dash_split

    def test_opening_brackets(self):
        moses = MosesTokenizer()

        text = "By the mid 1990s a version of the game became a Latvian television series (with a parliamentary setting, and played by Latvian celebrities)."

        # echo By the mid 1990s a version of the game became a Latvian television series (with a parliamentary setting, and played by Latvian celebrities). | perl mosesdecoder\scripts\tokenizer\tokenizer.perl en
        expected_tokens = "By the mid 1990s a version of the game became a Latvian television series ( with a parliamentary setting , and played by Latvian celebrities ) .".split()

        assert moses.tokenize(text) == expected_tokens

    def test_dot_splitting(self):
        moses = MosesTokenizer()
        text = "The meeting will take place at 11:00 a.m. Tuesday."
        expected_tokens = "The meeting will take place at 11 : 00 a.m. Tuesday .".split()
        self.assertEqual(moses.tokenize(text), expected_tokens)

    def test_trailing_dot_apostrophe(self):
        moses = MosesTokenizer()
        text = "'Hello.'"
        expected_tokens = "&apos;Hello . &apos;".split()
        self.assertEqual(moses.tokenize(text), expected_tokens)

    def test_protect_patterns(self):
        moses = MosesTokenizer()
        text = "this is a webpage https://stackoverflow.com/questions/6181381/how-to-print-variables-in-perl that kicks ass"
        expected_tokens = ['this', 'is', 'a', 'webpage',
                           'https://stackoverflow.com/questions/6181381/how-to-print-variables-in-perl',
                           'that', 'kicks', 'ass']
        assert moses.tokenize(text, protected_patterns=moses.BASIC_PROTECTED_PATTERNS) == expected_tokens

        # Testing against pattern from https://github.com/alvations/sacremoses/issues/35
        noe_patterns = [r'(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?))'
            r'(?::\d+)?'  # optional port
            r'(?:/\w+)*'
            r'(?:(?:\.[a-z]+)|/?)']
        assert moses.tokenize(text, protected_patterns=noe_patterns) == expected_tokens

class TestDetokenizer(unittest.TestCase):
    def test_moses_detokenize(self):
        mt = MosesTokenizer()
        md = MosesDetokenizer()

        text = u'This, is a sentence with weird\xbb symbols\u2026 appearing everywhere\xbf'
        expected_tokens = mt.tokenize(text)
        expected_detokens = u'This, is a sentence with weird \xbb symbols \u2026 appearing everywhere \xbf'

        assert md.detokenize(expected_tokens) == expected_detokens

        text = "This ain't funny. It's actually hillarious, yet double Ls. | [] < > [ ] & You're gonna shake it off? Don't?"
        expected_tokens = [u'This', u'ain', u'&apos;t', u'funny', u'.', u'It', u'&apos;s', u'actually', u'hillarious', u',', u'yet', u'double', u'Ls', u'.', u'&#124;', u'&#91;', u'&#93;', u'&lt;', u'&gt;', u'&#91;', u'&#93;', u'&amp;', u'You', u'&apos;re', u'gonna', u'shake', u'it', u'off', u'?', u'Don', u'&apos;t', u'?']
        expected_detokens = "This ain't funny. It's actually hillarious, yet double Ls. | [] < > [] & You're gonna shake it off? Don't?"
        assert mt.tokenize(text) == expected_tokens
        assert md.detokenize(expected_tokens) == expected_detokens

    def test_detokenize_with_aggressive_split(self):
        mt = MosesTokenizer()
        md = MosesDetokenizer()

        text = 'foo-bar'
        assert md.detokenize(mt.tokenize(text, aggressive_dash_splits=True)) == text

    def test_opening_brackets(self):
        tokenizer = MosesTokenizer()
        detokenizer = MosesDetokenizer()

        text = "By the mid 1990s a version of the game became a Latvian television series (with a parliamentary setting, and played by Latvian celebrities)."
        assert detokenizer.detokenize(tokenizer.tokenize(text)) == text

    def test_french_apostrophes(self):
        tokenizer = MosesTokenizer(lang='fr')
        detokenizer = MosesDetokenizer(lang='fr')

        text = u"L'amitié nous a fait forts d'esprit"
        assert detokenizer.detokenize(tokenizer.tokenize(text)) == text
