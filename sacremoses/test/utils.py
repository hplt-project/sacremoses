# -*- coding: utf-8 -*-

import os
import sys
import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(levelname)s: %(message)s')

try: # Python3
    import urllib.request as remote
except ImportError: # Python2
    import urllib as remote

import sacremoses.test.constants as C


def download_file(url, destination):
    """
    Downloads a file from the web to a local destination.
    """
    logging.info("Downloading %s", url)
    remote.urlretrieve(url, destination)


def file_exists(path):
    """
    Checks if a local file exists.
    """
    return os.path.isfile(path)


def download_file_if_not_exists(url, destination):
    """
    Downloads a file from the web to a local destination, if it does not exist.
    """
    if not file_exists(destination):
        download_file(url, destination)


def get_test_file(identifier):
    """
    Returns the local path to the test file with the given identifier. Downloads
    the file if needed.
    """
    url, destination = C.TEST_FILE[identifier]
    download_file_if_not_exists(url, destination)
    return destination
