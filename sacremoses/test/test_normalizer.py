# -*- coding: utf-8 -*-

"""
Tests for MosesTokenizer
"""

import unittest

from sacremoses.normalize import MosesPunctNormalizer


class TestNormalizer(unittest.TestCase):
    def test_moses_normalize_documents(self):
        moses = MosesPunctNormalizer()
        # Examples from normalizing big.txt
        inputs = [
            "The United States in 1805 (color map)                 _Facing_     193",
            "=Formation of the Constitution.=--(1) The plans before the convention,",
            "directions--(1) The infective element must be eliminated. When the ulcer",
            "College of Surgeons, Edinburgh.)]",
        ]
        expected = [
            "The United States in 1805 (color map) _Facing_ 193",
            "=Formation of the Constitution.=-- (1) The plans before the convention,",
            "directions-- (1) The infective element must be eliminated. When the ulcer",
            "College of Surgeons, Edinburgh.) ]",
        ]
        for text, expect in zip(inputs, expected):
            assert moses.normalize(text) == expect

    def test_moses_normalize_quote_comma(self):
        moses_norm_quote = MosesPunctNormalizer("en", norm_quote_commas=True)
        moses_no_norm_quote = MosesPunctNormalizer("en", norm_quote_commas=False)
        text = 'THIS EBOOK IS OTHERWISE PROVIDED TO YOU "AS-IS".'

        expected_norm_quote = 'THIS EBOOK IS OTHERWISE PROVIDED TO YOU "AS-IS."'
        assert moses_norm_quote.normalize(text) == expected_norm_quote

        expected_no_norm_quote = 'THIS EBOOK IS OTHERWISE PROVIDED TO YOU "AS-IS".'
        assert moses_no_norm_quote.normalize(text) == expected_no_norm_quote

    def test_moses_normalize_numbers(self):
        # See https://stackoverflow.com/a/55233871/610569
        moses_norm_num = MosesPunctNormalizer("en", norm_numbers=True)
        moses_no_norm_num = MosesPunctNormalizer("en", norm_numbers=False)

        text = "12{}123".format("\u00A0")
        expected = "12.123"
        assert moses_norm_num.normalize(text) == expected

        text = expected = "12 123"
        assert moses_no_norm_num.normalize(text) == expected

    def test_moses_noralize_single_apostrophe(self):
        moses_norm_num = MosesPunctNormalizer("en")
        text = "yesterday ’s reception"
        expected = "yesterday 's reception"
        assert moses_norm_num.normalize(text) == expected

    def test_replace_unicode_punct(self):
        moses_norm_unicode = MosesPunctNormalizer()
        text = "０《１２３》 ４５６％ 【７８９】"
        expected = '0"123" 456% [789]'
        assert moses_norm_unicode.replace_unicode_punct(text) == expected

    def test_normalization_pipeline(self):
        moses_norm_unicode = MosesPunctNormalizer(
            pre_replace_unicode_punct=True, post_remove_control_chars=True
        )
        text = "０《１２３》      ４５６％  '' 【７８９】"
        expected = '0"123" 456% " [789]'
        assert moses_norm_unicode.normalize(text) == expected
