# Sacremoses

[![Build Status](https://travis-ci.org/alvations/sacremoses.svg?branch=master)](https://travis-ci.org/alvations/sacremoses)
[![Build status](https://ci.appveyor.com/api/projects/status/bwgmj4axw9pdk1oq?svg=true)](https://ci.appveyor.com/project/alvations/sacremoses)

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
>>> mt = MosesTokenizer(lang='en')
>>> text = u'This, is a sentence with weird\xbb symbols\u2026 appearing everywhere\xbf'
>>> expected_tokenized = u'This , is a sentence with weird \xbb symbols \u2026 appearing everywhere \xbf'
>>> tokenized_text = mt.tokenize(text, return_str=True)
>>> tokenized_text == expected_tokenized
True


>>> mt, md = MosesTokenizer(lang='en'), MosesDetokenizer(lang='en')
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
>>> mtok = MosesTokenizer(lang='en')

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
>>> mtr.truecase("THE ADVENTURES OF SHERLOCK HOLMES", return_str=True)
'the ADVENTURES OF SHERLOCK HOLMES'
>>> mtr.truecase("THE ADVENTURES OF SHERLOCK HOLMES", return_str=True, use_known=True)
'the adventures of Sherlock Holmes'
```

**Normalizer**

```python
>>> from sacremoses import MosesPunctNormalizer
>>> mpn = MosesPunctNormalizer()
>>> mpn.normalize('THIS EBOOK IS OTHERWISE PROVIDED TO YOU "AS-IS."')
'THIS EBOOK IS OTHERWISE PROVIDED TO YOU "AS-IS."'
```


Usage (CLI)
====



```shell
$ pip install -U sacremoses>=0.0.34

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

```shell
$ sacremoses tokenize --help
Usage: sacremoses tokenize [OPTIONS]

Options:
  -l, --language TEXT            Use language specific rules when tokenizing
  -j, --processes INTEGER        No. of processes.
  -a, --aggressive-dash-splits   Triggers dash split rules.
  -x, --xml-escape               Escape special characters for XML.
  -p, --protected-patterns TEXT  Specify file with patters to be protected in
                                 tokenisation.
  -c, --custom-nb-prefixes TEXT  Specify a custom non-breaking prefixes file,
                                 add prefixes to the default ones from the
                                 specified language.
  -e, --encoding TEXT            Specify encoding of file.
  -h, --help                     Show this message and exit.


 $ sacremoses tokenize -j 4 < big.txt > big.txt.tok
100%|██████████████████████████████████| 128457/128457 [00:05<00:00, 24363.39it/s

 $ wget https://raw.githubusercontent.com/moses-smt/mosesdecoder/master/scripts/tokenizer/basic-protected-patterns
 $ sacremoses tokenize -j 4 -p basic-protected-patterns < big.txt > big.txt.tok
100%|██████████████████████████████████| 128457/128457 [00:05<00:00, 22183.94it/s
 ```

 **Detokenizer**

```shell
$ sacremoses detokenize --help
Usage: sacremoses detokenize [OPTIONS]

Options:
  -l, --language TEXT      Use language specific rules when tokenizing
  -j, --processes INTEGER  No. of processes.
  -x, --xml-unescape       Unescape special characters for XML.
  -e, --encoding TEXT      Specify encoding of file.
  -h, --help               Show this message and exit.


 $ sacremoses detokenize -j 4 < big.txt.tok > big.txt.tok.detok
128457it [00:23, 5355.88it/s]
```

 **Train Truecaser**

```shell
 $ sacremoses train-truecase --help
Usage: sacremoses train-truecase [OPTIONS]

Options:
  -m, --modelfile TEXT            Filename to save the modelfile.  [required]
  -j, --processes INTEGER         No. of processes.
  -a, --is-asr                    A flag to indicate that model is for ASR.
  -p, --possibly-use-first-token  Use the first token as part of truecasing.
  -e, --encoding TEXT      Specify encoding of file.
  -h, --help                      Show this message and exit.

$ sacremoses train-truecase -m big.model -j 4 < big.txt.tok
128457it [00:12, 10049.23it/s]
```

**Truecase**

```shell
$ sacremoses truecase --help
Usage: sacremoses truecase [OPTIONS]

Options:
  -m, --modelfile TEXT     The trucaser modelfile to use.  [required]
  -j, --processes INTEGER  No. of processes.
  -a, --is-asr             A flag to indicate that model is for ASR.
  -e, --encoding TEXT      Specify encoding of file.
  -h, --help               Show this message and exit.

$ sacremoses truecase -m big.model -j 4 < big.txt.tok > big.txt.tok.true
128457it [00:11, 11411.07it/s]
```

**Detruecase**

```shell
$ sacremoses detruecase --help
Usage: sacremoses detruecase [OPTIONS]

Options:
  -j, --processes INTEGER  No. of processes.
  -a, --is-headline        Whether the file are headlines.
  -e, --encoding TEXT      Specify encoding of file.
  -h, --help               Show this message and exit.

$ sacremoses detruecase -j 4 < big.txt.tok.true > big.txt.tok.true.detrue
100%|█████████████████████████████████| 128457/128457 [00:04<00:00, 26945.16it/s]
```

**Normalize**

```shell
$ sacremoses normalize --help
Usage: sacremoses normalize [OPTIONS]

Options:
  -l, --language TEXT           Use language specific rules when normalizing.
  -j, --processes INTEGER       No. of processes.
  -q, --normalize-quote-commas  Normalize quotations and commas.
  -d, --normalize-numbers       Normalize number.
  -e, --encoding TEXT           Specify encoding of file.
  -h, --help                    Show this message and exit.

$ sacremoses normalize -j 4 < big.txt > big.txt.norm.cli
100%|██████████████████████████████████| 128457/128457 [00:09<00:00, 13096.23it/s]
```
