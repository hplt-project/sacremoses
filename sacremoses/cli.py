# -*- coding: utf-8 -*-

from functools import partial
from itertools import chain

from tqdm import tqdm

import click

from sacremoses.tokenize import MosesTokenizer, MosesDetokenizer
from sacremoses.truecase import MosesTruecaser, MosesDetruecaser
from sacremoses.util import parallelize_preprocess

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def cli():
    pass

@cli.command('tokenize')
@click.option('--processes', '-j', default=1, help='No. of processes.')
@click.option('--aggressive-dash-splits', '-a', default=False, is_flag=True,
                help='Triggers dash split rules.')
@click.option('--xml-escape', '-x', default=True, is_flag=True,
                help='Escape special characters for XML.')
def tokenize_file(processes, xml_escape, aggressive_dash_splits):
    moses = MosesTokenizer()
    moses_tokenize = partial(moses.tokenize,
                        return_str=True,
                        aggressive_dash_splits=aggressive_dash_splits,
                        escape=xml_escape)

    with click.get_text_stream('stdin') as fin, click.get_text_stream('stdout') as fout:
        # If it's single process, joblib parallization is slower,
        # so just process line by line normally.
        if processes == 1:
            for line in tqdm(fin.readlines()):
                print(moses_tokenize(line), end='\n', file=fout)
        else:
            for outline in parallelize_preprocess(moses_tokenize, fin.readlines(), processes, progress_bar=True):
                print(outline, end='\n', file=fout)


@cli.command('detokenize')
@click.option('--processes', '-j', default=1, help='No. of processes.')
@click.option('--xml-unescape', '-x', default=True, is_flag=True,
                help='Unescape special characters for XML.')
def detokenize_file(processes, xml_unescape):
    moses = MosesDetokenizer()
    moses_detokenize = partial(moses.detokenize,
                        return_str=True,
                        unescape=xml_unescape)
    with click.get_text_stream('stdin') as fin, click.get_text_stream('stdout') as fout:
        # If it's single process, joblib parallization is slower,
        # so just process line by line normally.
        if processes == 1:
            for line in tqdm(fin.readlines()):
                print(moses_detokenize(line), end='\n', file=fout)
        else:
            document_iterator = map(str.split, fin.readlines())
            for outline in parallelize_preprocess(moses_detokenize, document_iterator, processes, progress_bar=True):
                print(outline, end='\n', file=fout)


@cli.command('train-truecase')
@click.option('--modelfile', '-m', required=True, help='Filename to save the modelfile.')
@click.option('--processes', '-j', default=1, help='No. of processes.')
@click.option('--is-asr', '-a',  default=False, is_flag=True,
                help='A flag to indicate that model is for ASR.')
@click.option('--possibly-use-first-token', '-p', default=False, is_flag=True,
                help='Use the first token as part of truecasing.')
def train_truecaser(modelfile, processes, is_asr, possibly_use_first_token):
    moses = MosesTruecaser(is_asr=is_asr)
    with click.get_text_stream('stdin') as fin:
        model = moses.train_from_file_object(fin,
                    possibly_use_first_token=possibly_use_first_token,
                    processes=processes)
        moses.save_model(modelfile)


@cli.command('truecase')
@click.option('--modelfile', '-m', required=True, help='The trucaser modelfile to use.')
@click.option('--processes', '-j', default=1, help='No. of processes.')
@click.option('--is-asr', '-a',  default=False, is_flag=True,
                help='A flag to indicate that model is for ASR.')
def truecase_file(modelfile, processes, is_asr):
    moses = MosesTruecaser(load_from=modelfile, is_asr=is_asr)
    with click.get_text_stream('stdin') as fin, click.get_text_stream('stdout') as fout:
        for line in tqdm(fin):
            print(moses.truecase(line, return_str=True), end='\n', file=fout)


@cli.command('detruecase')
@click.option('--processes', '-j', default=1, help='No. of processes.')
@click.option('--is-headline', '-a',  default=False, is_flag=True,
                help='Whether the file are headlines.')
def detruecase_file(processes, is_headline):
    moses = MosesDetruecaser()
    moses_detruecase = partial(moses.detruecase,
                        return_str=True,
                        is_headline=is_headline)
    with click.get_text_stream('stdin') as fin, click.get_text_stream('stdout') as fout:
        # If it's single process, joblib parallization is slower,
        # so just process line by line normally.
        if processes == 1:
            for line in tqdm(fin.readlines()):
                print(moses_detruecase(line), end='\n', file=fout)
        else:
            for outline in parallelize_preprocess(moses_detruecase, fin.readlines(), processes, progress_bar=True):
                print(outline, end='\n', file=fout)
