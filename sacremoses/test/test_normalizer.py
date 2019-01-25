# -*- coding: utf-8 -*-

"""
Tests for MosesPunctuationNormalizer
"""

import os
import unittest
import subprocess

from sacremoses.normalize import MosesPunctuationNormalizer

from sacremoses.test.utils import download_file_if_not_exists, get_test_file
import sacremoses.test.constants as C


class TestMosesPunctuationNormalizer(unittest.TestCase):

    def setUp(self):
        # Download original Perl script if needed
        download_file_if_not_exists(C.MOSES_NORMALIZER_SCRIPT_URL,
                                    C.MOSES_NORMALIZER_SCRIPT_LOCAL_PATH)

    def _create_gold(self, test_file, language='en', penn=False):
        """
        Normalizes a file with the original Perl script and returns the path
        to the normalized file.
        """
        flags = []
        if language:
            flags += ['-l', language]
        if penn:
            flags += ['-p']
        command = ['perl', C.MOSES_NORMALIZER_SCRIPT_LOCAL_PATH] + flags
        path_gold = '.'.join([test_file, 'normalized', 'gold'] + flags)
        with open(test_file) as stdin, open(path_gold, 'w') as stdout:
            process = subprocess.Popen(command, stdin=stdin, stdout=stdout)
            process.wait()
        return path_gold

    def _test_normalize(self, test_file, language='en', penn=False):
        """
        Compares MosesPunctuationNormalizer's output to the output of the
        original Perl script.
        """
        normalizer = MosesPunctuationNormalizer(language=language, penn=penn)
        # Normalize test file with original Perl script and given flags
        path_gold = self._create_gold(test_file, language, penn)
        # Compare to output of original Perl script
        with open(test_file) as u, open(path_gold) as g:
            for unnormalized, gold in zip(u, g):
                normalized = normalizer.normalize(unnormalized)
                self.assertEqual(normalized, gold)
        # Delete output of original Perl script
        os.remove(path_gold)

    def test_normalize_en(self):
        test_file = get_test_file('en')
        self._test_normalize(test_file=test_file, language='en', penn=False)

    def test_normalize_en_penn(self):
        test_file = get_test_file('en')
        self._test_normalize(test_file=test_file, language='en', penn=True)

    def test_normalize_de(self):
        test_file = get_test_file('de')
        self._test_normalize(test_file=test_file, language='de', penn=False)

    def test_normalize_de_penn(self):
        test_file = get_test_file('de')
        self._test_normalize(test_file=test_file, language='de', penn=True)

    # TODO: add tests for other languages


if __name__ == '__main__':
    unittest.main()
