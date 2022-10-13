# -*- coding: utf-8 -*-

"""
Tests for corpus.py
"""

import sys
import doctest
import unittest

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
                        isinstance(char, str)
                        for char in perluniprops.chars(category=category)
                    ),
                    True,
                )

    def test_perluniprops_chars_manual(self):
        perluniprops = corpus.Perluniprops()
        self.assertListEqual(
            list(perluniprops.chars("Open_Punctuation"))[:5],
            ["(", "[", "{", "\u0f3a", "\u0f3c"],
        )
        self.assertListEqual(
            list(perluniprops.chars("Currency_Symbol"))[:5],
            ["$", "\xa2", "\xa3", "\xa4", "\xa5"],
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
                        isinstance(word, str)
                        for word in nonbreaking_prefixes.words(lang=language)
                    ),
                    True,
                )

    def test_nonbreaking_prefixes_manual(self):
        nonbreaking_prefixes = corpus.NonbreakingPrefixes()
        self.assertListEqual(
            list(nonbreaking_prefixes.words("en"))[:10],
            ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"],
        )
        self.assertListEqual(
            list(nonbreaking_prefixes.words("ta"))[:5],
            ["\u0bb0", "\u0bc2", "\u0ba4\u0bbf\u0bb0\u0bc1", "\u0b8f", "\u0baa\u0bc0"],
        )


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(corpus))
    return tests
