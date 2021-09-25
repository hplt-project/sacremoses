import re
import time

import unittest
from collections import defaultdict

from sacremoses.corpus import NonbreakingPrefixes
from sacremoses.tokenize import MosesTokenizer

class HasNumericOnlyPatched(unittest.TestCase):
    def test_expected_num_only_prefixes(self):
        """Testing if the functionality of the NUMERIC_ONLY_PREFIXES parsing is the same without redos-able regex."""
        expected_prefixes = {'as': [], 'bn': [], 'ca': [], 'cs': [], 'de': [], 'el': [], 
                             'en': [('No', 'No #NUMERIC_ONLY#'), ('Art', 'Art #NUMERIC_ONLY#'), 
                                    ('pp', 'pp #NUMERIC_ONLY#')], 
                             'es': [], 'et': [], 'fi': [], 'fr': [], 
                             'ga': [('lch', 'lch #NUMERIC_ONLY#'), ('lgh', 'lgh #NUMERIC_ONLY#'), 
                                    ('uimh', 'uimh #NUMERIC_ONLY#')], 
                             'gu': [], 'hi': [], 
                             'hu': [('jan', 'jan #NUMERIC_ONLY#'), ('Jan', 'Jan #NUMERIC_ONLY#'), 
                                    ('Feb', 'Feb #NUMERIC_ONLY#'), ('feb', 'feb #NUMERIC_ONLY#'), 
                                    ('márc', 'márc #NUMERIC_ONLY#'), ('Márc', 'Márc #NUMERIC_ONLY#'), 
                                    ('ápr', 'ápr #NUMERIC_ONLY#'), ('Ápr', 'Ápr #NUMERIC_ONLY#'), 
                                    ('máj', 'máj #NUMERIC_ONLY#'), ('Máj', 'Máj #NUMERIC_ONLY#'),
                                    ('jún', 'jún #NUMERIC_ONLY#'), ('Jún', 'Jún #NUMERIC_ONLY#'), 
                                    ('Júl', 'Júl #NUMERIC_ONLY#'), ('júl', 'júl #NUMERIC_ONLY#'), 
                                    ('aug', 'aug #NUMERIC_ONLY#'), ('Aug', 'Aug #NUMERIC_ONLY#'), 
                                    ('Szept', 'Szept #NUMERIC_ONLY#'), ('szept', 'szept #NUMERIC_ONLY#'), 
                                    ('okt', 'okt #NUMERIC_ONLY#'), ('Okt', 'Okt #NUMERIC_ONLY#'), 
                                    ('nov', 'nov #NUMERIC_ONLY#'), ('Nov', 'Nov #NUMERIC_ONLY#'), 
                                    ('dec', 'dec #NUMERIC_ONLY#'), ('Dec', 'Dec #NUMERIC_ONLY#'), 
                                    ('tel', 'tel #NUMERIC_ONLY#'), ('Tel', 'Tel #NUMERIC_ONLY#'), 
                                    ('Fax', 'Fax #NUMERIC_ONLY#'), ('fax', 'fax #NUMERIC_ONLY#')], 
                             'is': [('no', 'no #NUMERIC_ONLY#'), ('No', 'No #NUMERIC_ONLY#'), 
                                    ('nr', 'nr #NUMERIC_ONLY#'), ('Nr', 'Nr #NUMERIC_ONLY#'), 
                                    ('nR', 'nR #NUMERIC_ONLY#'), ('NR', 'NR #NUMERIC_ONLY#')], 
                             'it': [('No', 'No #NUMERIC_ONLY#'), ('Art', 'Art #NUMERIC_ONLY#'), 
                                    ('pp', 'pp #NUMERIC_ONLY#')], 'kn': [], 
                             'lt': [('No', 'No #NUMERIC_ONLY#')], 
                             'lv': [('Nr', 'Nr #NUMERIC_ONLY#')], 
                             'ml': [], 'mni': [], 'mr': [], 
                             'nl': [('Nr', 'Nr #NUMERIC_ONLY#'), ('nr', 'nr #NUMERIC_ONLY#')], 
                             'or': [], 'pa': [], 
                             'pl': [('nr', 'nr #NUMERIC_ONLY#'), ('Nr', 'Nr #NUMERIC_ONLY#'), 
                                    ('pkt', 'pkt #NUMERIC_ONLY#'), ('str', 'str #NUMERIC_ONLY#'), 
                                    ('tab', 'tab #NUMERIC_ONLY#'), ('Tab', 'Tab #NUMERIC_ONLY#'), 
                                    ('ust', 'ust #NUMERIC_ONLY#'), ('par', 'par #NUMERIC_ONLY#'),
                                    ('r', 'r #NUMERIC_ONLY#'), ('l', 'l #NUMERIC_ONLY#'),
                                    ('s', 's #NUMERIC_ONLY#')], 
                             'pt': [('No', 'No #NUMERIC_ONLY#'), ('Art', 'Art #NUMERIC_ONLY#'), 
                                    ('p', 'p #NUMERIC_ONLY#'), ('pp', 'pp #NUMERIC_ONLY#')], 
                             'ro': [], 'ru': [], 'sk': [], 
                             'sl': [('št', 'št #NUMERIC_ONLY#'), ('Št', 'Št #NUMERIC_ONLY#')], 
                             'sv': [], 'ta': [], 'te': [], 
                             'tdt': [('No', 'No #NUMERIC_ONLY#'), ('Art', 'Art #NUMERIC_ONLY#'), 
                                     ('p', 'p #NUMERIC_ONLY#'), ('pp', 'pp #NUMERIC_ONLY#')], 
                             'yue': [('No', 'No #NUMERIC_ONLY#'), ('Nr', 'Nr #NUMERIC_ONLY#')], 
                             'zh': [('No', 'No #NUMERIC_ONLY#'), ('Nr', 'Nr #NUMERIC_ONLY#')]}

        nonbreaking_prefixes = NonbreakingPrefixes()
        moses = MosesTokenizer()
        lang2numonlyprefix = defaultdict(list)
        
        
        for lang in nonbreaking_prefixes.available_langs.values():    
            lang2numonlyprefix[lang] = [(w.rpartition(" ")[0], w) 
                for w in nonbreaking_prefixes.words(lang) if moses.has_numeric_only(w)]
            
        assert lang2numonlyprefix == expected_prefixes
        
        
    def test_stress_has_numeric_only_prefixes(self):
        """Stress testing to prevent redos."""
        moses = MosesTokenizer()
        for i in range(1, 10):
            start_time = time.perf_counter()
            payload = " " + " " * (i*500) + ""
            moses.has_numeric_only(payload)
            stop_time = time.perf_counter() - start_time
            assert stop_time < 20
        
