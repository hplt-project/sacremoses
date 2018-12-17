# Sacremoses

[![Build Status](https://travis-ci.org/alvations/sacremoses.svg?branch=master)](https://travis-ci.org/alvations/sacremoses)

License
====

GNU Lesser General Public License version 2.1 or, at your option, any later version.

Install
====

```
pip install -U sacremoses
```

Usage
====

**Tokenizer and Detokenizer**

```python
>>> from sacremoses import MosesTokenizer, MosesDetokenizer
>>> mt = MosesTokenizer()
>>> text = u'This, is a sentence with weird\xbb symbols\u2026 appearing everywhere\xbf'
>>> expected_tokenized = u'This , is a sentence with weird \xbb symbols \u2026 appearing everywhere \xbf'
>>> tokenized_text = mt.tokenize(text, return_str=True)
>>> tokenized_text == expected_tokenized
True


>>> mt, md = MosesTokenizer(), MosesDetokenizer()
>>> sent = "This ain't funny. It's actually hillarious, yet double Ls. | [] < > [ ] & You're gonna shake it off? Don't?"
>>> expected_tokens = [u'This', u'ain', u'&apos;t', u'funny', u'.', u'It', u'&apos;s', u'actually', u'hillarious', u',', u'yet', u'double', u'Ls', u'.', u'&#124;', u'&#91;', u'&#93;', u'&lt;', u'&gt;', u'&#91;', u'&#93;', u'&amp;', u'You', u'&apos;re', u'gonna', u'shake', u'it', u'off', u'?', u'Don', u'&apos;t', u'?']
>>> expected_detokens = "This ain't funny. It's actually hillarious, yet double Ls. | [] < > [] & You're gonna shake it off? Don't?"
>>> mt.tokenize(sent) == expected_tokens
True
>>> md.detokenize(tokens) == expected_detokens
True
```


**Truecaser**

```python
>>> from sacremoses import MosesTruecaser

# Train a new truecaser from a 'big.txt' file.
>>> mtr = MosesTruecaser()
>>> mtr.train_from_file('big.txt)

# Save the truecase model to 'big.truecasemodel' using `save_to`
>>> mtr = MosesTruecaser()
>>> mtr.train_from_file('big.txt', save_to='big.truecasemodel')

# Save the truecase model to 'big.truecasemodel' after training
# (just in case you forgot to use `save_to`)
>>> mtr = MosesTruecaser()
>>> mtr.train('big.txt')
>>> mtr._save_model('big.truecasemodel')

# Truecase a string using trained model.
>>> mtr = MosesTruecaser()
>>> mtr.train('big.txt')
>>> mtr.truecase("THE ADVENTURES OF SHERLOCK HOLMES")
['the', 'adventures', 'of', 'Sherlock', 'Holmes']
>>> print(mtr.truecase("THE ADVENTURES OF SHERLOCK HOLMES", return_str=True)
'the adventures of Sherlock Holmes'

# Truecase a file using trained model.
>>> mtr = MosesTruecaser()
>>> mtr.train('big.txt')
>>> list(mtr.truecase_file('big.txt')) # Returns one sentence per line.

# Write to a truecase_file output to a file.
>>> mtr = MosesTruecaser()
>>> mtr.train('big.txt')
>>> with open('big.truecased', 'w') as fout:
...     fout.write('\n'.join(mtr.truecase_file('big.txt')))

# Load the truecase model from 'big.truecasemodel'
>>> mtr = MosesTruecaser('big.truecasemodel')
>>> mtr.truecase("THE ADVENTURES OF SHERLOCK HOLMES")
['the', 'adventures', 'of', 'Sherlock', 'Holmes']

```
