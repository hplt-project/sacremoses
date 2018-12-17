# -*- coding: utf-8 -*-

"""
Tests for MosesTokenizer
"""

import os
import unittest

from sacremoses.truecase import MosesTruecaser


# Crazy hack to support Python2 and 3 and requests to download files.
# From https://stackoverflow.com/a/47897956/610569
try: # Try importing Python3 urllib
    import urllib.request
except AttributeError: # Now importing Python2 urllib
    import urllib

def get_content(url):
    try: # Using Python3 urllib.
        with urllib.request.urlopen(url) as response:
            return response.read() # Returns http.client.HTTPResponse.
    except AttributeError: # Using Python3 urllib.
        return urllib.urlopen(url).read() # Returns an instance.


class TestTokenzier(unittest.TestCase):
    def test_moses_truecase_documents(self):
        moses = MosesTruecaser()
        # Train the model from documents.
        docs = [line.split() for line in self.big_txt.split('\n')]
        moses.train(docs)
        # Test all self.input_output test cases.
        for _input, _output in self.input_output.items():
            assert moses.truecase(_input) == _output

    def test_moses_truecase_file(self):
        moses = MosesTruecaser()
        # Train the model from file.
        moses.train_from_file('big.txt')
        # Test all self.input_output test cases.
        for _input, _output in self.input_output.items():
            assert moses.truecase(_input) == _output

    def setUp(self):
        # Check if the Norvig's big.txt file exists.
        if os.path.isfile('big.txt'):
            with open('big.txt') as fin:
                self.big_txt = fin.read()
        else: # Otherwise, download the big.txt.
            self.big_txt = get_content("https://norvig.com/big.txt").decode('utf8')
            with open('big.txt', 'w') as fout:
                fout.write(self.big_txt)

        # Test case where inputs are all caps.
        caps_input = "THE ADVENTURES OF SHERLOCK HOLMES"
        expected_caps_output = ['the', 'adventures', 'of', 'Sherlock', 'Holmes']

        # Test normal input to truecase.
        normal_input = str('You can also find out about how to make a donation '
                           'to Project Gutenberg, and how to get involved.')
        expecte_normal_output = ['you', 'can', 'also', 'find', 'out', 'about',
                                'how', 'to', 'make', 'a', 'donation', 'to',
                                'Project', 'Gutenberg,', 'and', 'how', 'to',
                                'get', 'involved.']

        # Keep a key-value pairs of in/outputs.
        self.input_output = {caps_input: expected_caps_output,
                             normal_input: expecte_normal_output}
