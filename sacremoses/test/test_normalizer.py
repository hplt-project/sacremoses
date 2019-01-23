#/usr/bin/env python3

"""
Tests for MosesPunctuationNormalizer
"""

import unittest

from sacremoses.normalize import MosesPunctuationNormalizer


class TestMosesPunctuationNormalizer(unittest.TestCase):

    def test_normalize_de(self):
        normalizer = MosesPunctuationNormalizer('de')
        with open('corpus.de') as o, open('corpus.normalized.de') as n:
            for original, normalized in zip(o, n):
                self.assertEquals(normalizer.normalize(original), normalized)

    # TODO: add tests for other languages

    # TODO: add tests Penn Treebank style normalization


if __name__ == '__main__':
    unittest.main()
