# -*- coding: utf-8 -*-

"""
Tests for corpus.py
"""

import sys
import doctest
import unittest

from six import text_type

from sacremoses import corpus


class CorpusTest(unittest.TestCase):
    def test_perluniprops_chars_sanity_check(self):
        perluniprops = corpus.Perluniprops()
        for category in perluniprops.available_categories:
            if sys.version_info[0] >= 3:  # Python 3
                with self.subTest(category=category):
                    count = 0
                    for char in perluniprops.chars(category=category):
                        self.assertIsInstance(char, str)
                        count += 1
                    self.assertGreater(count, 0)
            else:
                self.assertEqual(
                    all(
                        isinstance(char, text_type)
                        for char in perluniprops.chars(category=category)
                    ),
                    True,
                )

    def test_perluniprops_chars_manual(self):
        perluniprops = corpus.Perluniprops()
        self.assertListEqual(
            list(perluniprops.chars("Open_Punctuation"))[:5],
            [u"(", u"[", u"{", u"\u0f3a", u"\u0f3c"],
        )
        self.assertListEqual(
            list(perluniprops.chars("Currency_Symbol"))[:5],
            [u"$", u"\xa2", u"\xa3", u"\xa4", u"\xa5"],
        )

    def test_nonbreaking_prefixes_sanity_check(self):
        nonbreaking_prefixes = corpus.NonbreakingPrefixes()
        for language in nonbreaking_prefixes.available_langs.values():
            if sys.version_info[0] >= 3:  # Python 3
                with self.subTest(language=language):
                    count = 0
                    for word in nonbreaking_prefixes.words(lang=language):
                        self.assertIsInstance(word, str)
                        count += 1
                    self.assertGreater(count, 0)
            else:
                self.assertEqual(
                    all(
                        isinstance(word, text_type)
                        for word in nonbreaking_prefixes.words(lang=language)
                    ),
                    True,
                )

    def test_nonbreaking_prefixes_manual(self):
        nonbreaking_prefixes = corpus.NonbreakingPrefixes()
        self.assertListEqual(
            list(nonbreaking_prefixes.words("en"))[:10],
            [u"A", u"B", u"C", u"D", u"E", u"F", u"G", u"H", u"I", u"J"],
        )
        self.assertListEqual(
            list(nonbreaking_prefixes.words("ta"))[:5],
            [u"\u0b85", u"\u0b86", u"\u0b87", u"\u0b88", u"\u0b89"],
        )


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(corpus))
    return tests
