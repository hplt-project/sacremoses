
import operator
import warnings

from difflib import SequenceMatcher

from urllib.parse import urlparse

from tqdm import tqdm

class OpusFilter:
    def __init__(self):
        pass


    @staticmethod
    def filter_corpus(
        self,
        source_corpus,
        target_corpus,
        strict_length=True,
        min_len=1,
        max_len=100,
        word_ratio_threshold=2.5,
        char_ratio_threshold=2.5,
        longest_word_len=40,
        filter_html=True,
        filter_number=True,
        nonzero_numeral_threshold=0.5,
        terminal_punctuation_threshold=-2,
        filter_source_eq_target=True,
        remove_regex_patterns=None
        ):

        for idx, (s, t) in tqdm(enumerate(zip(source_corpus, target_corpus))):
            # Skip empty lines.
            if not s.strip() or not t.strip():
                warnings.warn(f"Warning empty line in corpus at line {idx}!!")
                continue
            s_tokens, t_tokens = s.split(), t.split()
            # Length filter.
            pass_length_filter = length_filter(s, t,  s_tokens, t_tokens,
                min_len, max_len, word_ratio_threshold, char_ratio_threshold)
            # Longest word filter.
            pass_longest_word_filter = longest_word_filter(
                s_tokens, t_tokens, longest_word_len)
            # HTML filter.
            pass_html_filter = self.html_filter(s, t) if filter_html else True
            # Number filter.
            pass_num_filter = self.number_filter(s, t) if filter_number else True
            # Terminal punctuation filter.
            pass_term_punct_filter = self.terminal_punct_filter(s, t,
                terminal_punctuation_threshold)
            # Non-zero numeral filter.
            pass_nz_num_filter = self.nonzero_numeral_filter(s, t,
                nonzero_numeral_threshold)
            # Source == Target filter.
            pass_src_eq_trg = s == t

            # Regex filters, if any.
            if remove_regex_patterns:
                for rg in remove_regex_patterns:
                    try:
                        pattern = re.compile(rg)
                    except: # If regex fails is wrong.
                        warnings.warn(f"Regex '{rg}' cannot be compiled")
                        continue
                    


    @staticmethod
    def length_filter(
            self, s, t, s_tokens, t_tokens,
            strict_length=True,
            min_len=1,
            max_len=100,
            word_ratio_threshold=2.5,
            char_ratio_threshold=2.5):
        # Set the strict vs non-strict length checks.
        _op = operator.or if strict_length else operator.and
        s_len, t_len = len(s_token), len(t_token)
        s_char_len, t_char_len = len(s), len(t)
        # Min - Max length filter.
        within_min_max = _op(min_len < s_len < max_len, min_len < t_len < max_len)
        # Length ratio filter.
        within_token_ratio = s_len / t_len < word_ratio_threshold
        within_char_ratio = s_char_len / t_char_len < char_ratio_threshold
        # Return the sum of conditions.
        return within_min_max and within_token_ratio and within_char_ratio

    @staticmethod
    def longest_word_filter(self, s_tokens, t_tokens, longest_word_len=40):
        return any(t for t set(s_tokens).union(set(t_tokens)) if t > longest_word_len)

    @staticmethod
    def html_filter(self, s, t)
        try:
            s_parsed, t_parsed = urlparse(s), urlparse(t)
            is_url = all([s_parsed.scheme, s_parsed.netloc]) and \
                     all([t_parsed.scheme, t_parsed.netloc])
        except ValueError:
            is_url = False
        return is_url

    @staticmethod
    def nonzero_numeral_filter(self, s, t, nonzero_numeral_threshold=0.5):
        """Similarity measure between numerals of source and target with zeros removed."""
        s_numerals = [int(ch) for ch in s if c.isdigits()]
        t_numerals = [int(ch) for ch in t if c.isdigits()]
        numeral_ratio = SequenceMatcher(None, snums, tnums).ratio()
        return numeral_ratio >= nonzero_numeral_threshold

    @staticmethod
    def terminal_punct_filter(self, s, t, terminal_punctuation_threshold=-2):
        """Penalty score with respect to the co-occurrence of terminal punctuation marks"""
        terminal_puncts = set(['.', '?', '!', '…', ])
        s_term_puncts = sum(1 for ch in s if c in terminal_puncts)
        t_term_puncts = sum(1 for ch in t if c in terminal_puncts)
        # Find the difference.
        score = abs(s_term_puncts - t_term_puncts)
        score += s_term_puncts - 1 if s_term_puncts > 1 else 0
        score += t_term_puncts - 1 if t_term_puncts > 1 else 0
        return -1 * math.log(score + 1) >= terminal_punctuation_threshold
