# -*- coding: utf-8 -*-

"""
Tests for MosesTokenizer
"""

import hashlib
import os
import unittest
import urllib.error
import urllib.request

from sacremoses.truecase import MosesTruecaser, MosesDetruecaser

#: Norvig's big.txt, the corpus these tests train a truecase model on. It is
#: fetched over the network and cached on disk -- and in CI, under a static
#: cache key -- so without an integrity check the suite trains on whatever
#: bytes the remote host happens to return, and a truecase model shapes the
#: capitalisation of everything downstream of it. Pinned by digest, not by URL.
BIG_TXT_SHA256 = "fa066c7d40f0f201ac4144e652aa62430e58a6b3805ec70650f678da5804e87b"
BIG_TXT_SIZE = 6488666


def get_content(url):
    with urllib.request.urlopen(url) as response:
        return response.read()  # Returns http.client.HTTPResponse.


def verify_big_txt(data):
    """Return ``data`` if it is the expected corpus, else raise.

    Raising rather than warning is deliberate: a silent fallback to unverified
    bytes is exactly the failure this check exists to prevent.
    """
    digest = hashlib.sha256(data).hexdigest()
    if len(data) != BIG_TXT_SIZE or digest != BIG_TXT_SHA256:
        raise ValueError(
            "big.txt failed verification: expected %d bytes / sha256 %s, "
            "got %d bytes / sha256 %s. Delete any cached big.txt and retry; "
            "if it persists, do not trust the source."
            % (BIG_TXT_SIZE, BIG_TXT_SHA256, len(data), digest)
        )
    return data


class TestTruecaser(unittest.TestCase):
    def test_moses_truecase_documents(self):
        moses = MosesTruecaser()
        # Train the model from documents.
        docs = [line.split() for line in self.big_txt.split("\n")]
        moses.train(docs)
        # Test all self.input_output test cases.
        for _input, _output in self.input_output.items():
            self.assertEqual(moses.truecase(_input), _output)

    def test_moses_truecase_file(self):
        moses = MosesTruecaser()
        # Train the model from file.
        moses.train_from_file("big.txt")
        # Test all self.input_output test cases.
        for _input, _output in self.input_output.items():
            self.assertEqual(moses.truecase(_input), _output)

    def setUp(self):
        # Check if the Norvig's big.txt file exists. A cached copy is verified
        # too -- it may be left over from an earlier unverified run, or from CI
        # restoring its cache.
        if os.path.isfile("big.txt"):
            with open("big.txt", "rb") as fin:
                raw = verify_big_txt(fin.read())
        else:  # Otherwise, download the big.txt.
            try:  # Download from the original norvig.com
                raw = verify_big_txt(get_content("https://norvig.com/big.txt"))
            except (urllib.error.URLError, OSError, ValueError):
                # Named exceptions, not a bare `except:` -- that swallowed
                # KeyboardInterrupt and, worse, turned a failed integrity check
                # into a silent fallback to the mirror.
                big_text_url = str(
                    "https://gist.githubusercontent.com/alvations/"
                    "6e878bab0eda2624167aa7ec13fc3e94/raw/"
                    "4fb3bac1da1ba7a172ff1936e96bee3bc8892931/"
                    "big.txt"
                )
                raw = verify_big_txt(get_content(big_text_url))
            # newline="" so Windows does not rewrite \n to \r\n and change the
            # digest of the file we just verified.
            with open("big.txt", "w", encoding="utf-8", newline="") as fout:
                fout.write(raw.decode("utf8"))
        self.big_txt = raw.decode("utf8")

        # Test case where inputs are all caps.
        caps_input = "THE ADVENTURES OF SHERLOCK HOLMES"
        expected_caps_output = ["the", "adventures", "of", "Sherlock", "Holmes"]

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

    def test_use_known(self):
        moses = MosesTruecaser()
        moses.train([
            ['Start', 'a', 'a', 'A', 'A', 'a', 'a', '.'], # 'a' is best, but 'A' is also known.
        ])
        self.assertEqual(moses.truecase('Start A .', use_known=False), ['Start', 'a', '.'])
        self.assertEqual(moses.truecase('Start A .', use_known=True), ['Start', 'A', '.'])

    def test_delayed_sentence_start(self):
        """Test that first word after delayed sentence start still holds, and
        thus ignores use_known for that particular token."""
        moses = MosesTruecaser()
        moses.train([
            ['Start', 'Start', 'start'] # 'Start' is best, but 'start' is okay.
        ])
        self.assertEqual(moses.truecase('" start start', use_known=True), ['"', 'Start', 'start'])


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

    def test_moses_detruecase_allcaps(self):
        moses = MosesDetruecaser()
        text = "MLB Baseball standings"
        expected = ["MLB", "Baseball", "standings"]
        expected_str = "MLB Baseball standings"
        assert moses.detruecase(text) == expected
        assert moses.detruecase(text, return_str=True) == expected_str
