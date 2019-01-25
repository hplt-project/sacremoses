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

Usage (Python)
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
>>> from sacremoses import MosesTruecaser, MosesTokenizer

# Train a new truecaser from a 'big.txt' file.
>>> mtr = MosesTruecaser()
>>> mtok = MosesTokenizer()

# Save the truecase model to 'big.truecasemodel' using `save_to`
>> tokenized_docs = [mtok.tokenize(line) for line in open('big.txt')]
>>> mtr.train(tokenized_docs, save_to='big.truecasemodel')

# Save the truecase model to 'big.truecasemodel' after training
# (just in case you forgot to use `save_to`)
>>> mtr = MosesTruecaser()
>>> mtr.train('big.txt')
>>> mtr.save_model('big.truecasemodel')

# Truecase a string after training a model.
>>> mtr = MosesTruecaser()
>>> mtr.train('big.txt')
>>> mtr.truecase("THE ADVENTURES OF SHERLOCK HOLMES")
['the', 'adventures', 'of', 'Sherlock', 'Holmes']

# Loads a model and truecase a string using trained model.
>>> mtr = MosesTruecaser('big.truecasemodel')
>>> mtr.truecase("THE ADVENTURES OF SHERLOCK HOLMES")
['the', 'adventures', 'of', 'Sherlock', 'Holmes']
>>> print(mtr.truecase("THE ADVENTURES OF SHERLOCK HOLMES", return_str=True)
'the adventures of Sherlock Holmes'
```


Usage (CLI)
====



```
$ pip install -U sacremoses>=0.07

$ sacremoses --help
Usage: sacremoses [OPTIONS] COMMAND [ARGS]...

Options:
  --version   Show the version and exit.
  -h, --help  Show this message and exit.

Commands:
  detokenize
  detruecase
  tokenize
  train-truecase
  truecase
```


**Tokenizer** 

```
$ sacremoses tokenize --help
Usage: sacremoses tokenize [OPTIONS]

Options:
  -j, --processes INTEGER       No. of processes.
  -a, --aggressive-dash-splits  Triggers dash split rules.
  -x, --xml-escape              Escape special characters for XML.
  -h, --help                    Show this message and exit.
 
 
 $ sacremoses tokenize -j 4 < big.txt > big.txt.tok
100%|██████████████████████████████████| 128457/128457 [00:15<00:00, 8059.72it/s]
 ```
 
 **Detokenizer**
 
 ```
 $ sacremoses detokenize --help
Usage: sacremoses detokenize [OPTIONS]

Options:
  -j, --processes INTEGER  No. of processes.
  -x, --xml-unescape       Unescape special characters for XML.
  -h, --help               Show this message and exit.
  
 
 $ sacremoses detokenize -j 4 < big.txt.tok > big.txt.tok.detok 
128457it [00:23, 5355.88it/s]
 ```
 
