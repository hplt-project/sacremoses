# -*- coding: utf-8 -*-

"""
Tests for MosesTokenizer
"""

import io
import os
import unittest

from six import text_type

from sacremoses.truecase import MosesTruecaser, MosesDetruecaser


# Crazy hack to support Python2 and 3 and requests to download files.
# From https://stackoverflow.com/a/47897956/610569
try:  # Try importing Python3 urllib
    import urllib.request
except ImportError:  # Now importing Python2 urllib
    import urllib


def get_content(url):
    try:  # Using Python3 urllib.
        with urllib.request.urlopen(url) as response:
            return response.read()  # Returns http.client.HTTPResponse.
    except AttributeError:  # Using Python3 urllib.
        return urllib.urlopen(url).read()  # Returns an instance.


class TestTruecaser(unittest.TestCase):
    def test_moses_truecase_documents(self):
        moses = MosesTruecaser()
        # Train the model from documents.
        docs = [line.split() for line in self.big_txt.split("\n")]
        moses.train(docs)
        # Test all self.input_output test cases.
        for _input, _output in self.input_output.items():
            assert moses.truecase(_input) == _output

    def test_moses_truecase_file(self):
        moses = MosesTruecaser()
        # Train the model from file.
        moses.train_from_file("big.txt")
        # Test all self.input_output test cases.
        for _input, _output in self.input_output.items():
            assert moses.truecase(_input) == _output

    def setUp(self):
        # Check if the Norvig's big.txt file exists.
        if os.path.isfile("big.txt"):
            with open("big.txt") as fin:
                self.big_txt = fin.read()
        else:  # Otherwise, download the big.txt.
            try:  # Download from the original norvig.com
                self.big_txt = get_content("https://norvig.com/big.txt").decode("utf8")
            except:  # Otherwise get it from the github gist mirror.
                big_text_url = str(
                    "https://gist.githubusercontent.com/alvations/"
                    "6e878bab0eda2624167aa7ec13fc3e94/raw/"
                    "4fb3bac1da1ba7a172ff1936e96bee3bc8892931/"
                    "big.txt"
                )
                self.big_text = get_content(big_text_url).decode("utf8")
            with open("big.txt", "w") as fout:
                fout.write(self.big_txt)

        # Test case where inputs are all caps.
        caps_input = "THE ADVENTURES OF SHERLOCK HOLMES"
        expected_caps_output = ["the", "ADVENTURES", "OF", "SHERLOCK", "HOLMES"]

        # Test normal input to truecase.
        normal_input = str(
            "You can also find out about how to make a donation "
            "to Project Gutenberg, and how to get involved."
        )
        expecte_normal_output = [
            "you",
            "can",
            "also",
            "find",
            "out",
            "about",
            "how",
            "to",
            "make",
            "a",
            "donation",
            "to",
            "Project",
            "Gutenberg,",
            "and",
            "how",
            "to",
            "get",
            "involved.",
        ]

        # Keep a key-value pairs of in/outputs.
        self.input_output = {
            caps_input: expected_caps_output,
            normal_input: expecte_normal_output,
        }


class TestDetruecaser(unittest.TestCase):
    def test_moses_detruecase_str(self):
        moses = MosesDetruecaser()
        text = "the adventures of Sherlock Holmes"
        expected = ["The", "adventures", "of", "Sherlock", "Holmes"]
        expected_str = "The adventures of Sherlock Holmes"
        assert moses.detruecase(text) == expected
        assert moses.detruecase(text, return_str=True) == expected_str

    def test_moses_detruecase_headline(self):
        moses = MosesDetruecaser()
        text = "the adventures of Sherlock Holmes"
        expected = ["The", "Adventures", "of", "Sherlock", "Holmes"]
        expected_str = "The Adventures of Sherlock Holmes"
        assert moses.detruecase(text, is_headline=True) == expected
        assert moses.detruecase(text, is_headline=True, return_str=True) == expected_str
