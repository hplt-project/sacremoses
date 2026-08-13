# -*- coding: utf-8 -*-

import os
from functools import partial
from functools import update_wrapper

import click

from sacremoses.tokenize import MosesTokenizer, MosesDetokenizer
from sacremoses.truecase import MosesTruecaser, MosesDetruecaser
from sacremoses.normalize import MosesPunctNormalizer
from sacremoses.util import parallelize_preprocess

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(chain=True, context_settings=CONTEXT_SETTINGS)
@click.option(
    "--language", "-l", default="en", help="Use language specific rules when tokenizing"
)
@click.option("--processes", "-j", default=1, help="No. of processes.")
@click.option("--encoding", "-e", default="utf8", help="Specify encoding of file.")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Disable progress bar."
)
@click.version_option()
def cli(language, encoding, processes, quiet):
    pass


@cli.result_callback()
def process_pipeline(processors, encoding, **kwargs):
    # NOTE: each stage is deliberately handed a `list`, not a lazy iterator.
    # Streaming would use less memory, but it would also change behaviour that
    # users can see:
    #   * `truecase` reads its input twice when the model file is missing (it
    #     trains on the input before truecasing it); a generator cannot be
    #     walked a second time.
    #   * `parallelize_preprocess()` wraps the input in `tqdm`, which only
    #     renders a percentage bar for a sized iterable. A generator would
    #     silently downgrade every progress bar to a bare counter.
    #   * with `-j` > 1, joblib collects all results before returning anyway,
    #     so streaming saves nothing there.
    # Keep the `list()` unless all three are addressed.
    with click.get_text_stream("stdin", encoding=encoding) as fin:
        iterator = fin  # Initialize fin as the first iterator.
        for proc in processors:
            iterator = proc(list(iterator), **kwargs)
        if iterator:
            for item in iterator:
                click.echo(item)


def processor(f, **kwargs):
    """Helper decorator to rewrite a function so that
    it returns another function from it.
    """

    def new_func(**kwargs):
        def processor(stream, **kwargs):
            return f(stream, **kwargs)

        return partial(processor, **kwargs)

    return update_wrapper(new_func, f, **kwargs)


#: Upper bound on patterns read from a --protected-patterns file.
MAX_PROTECTED_PATTERNS = 1000


def parallel_or_not(iterator, func, processes, quiet):
    if processes == 1:
        for line in iterator:
            yield func(line)
    else:
        for outline in parallelize_preprocess(
            func, iterator, processes, progress_bar=(not quiet)
        ):
            yield outline


########################################################################
# Tokenize
########################################################################


@cli.command("tokenize")
@click.option(
    "--aggressive-dash-splits",
    "-a",
    default=False,
    is_flag=True,
    help="Triggers dash split rules.",
)
@click.option(
    "--xml-escape",
    "-x",
    default=True,
    is_flag=True,
    help="Escape special characters for XML.",
)
@click.option(
    "--protected-patterns",
    "-p",
    help="Specify file with patters to be protected in tokenisation. Special values: :basic: :web:",
)
@click.option(
    "--custom-nb-prefixes",
    "-c",
    help="Specify a custom non-breaking prefixes file, add prefixes to the default ones from the specified language.",
)
@processor
def tokenize_file(
    iterator,
    language,
    processes,
    quiet,
    xml_escape,
    aggressive_dash_splits,
    protected_patterns,
    custom_nb_prefixes,
):
    moses = MosesTokenizer(
        lang=language, custom_nonbreaking_prefixes_file=custom_nb_prefixes
    )

    if protected_patterns:
        if protected_patterns == ":basic:":
            protected_patterns = moses.BASIC_PROTECTED_PATTERNS
        elif protected_patterns == ":web:":
            protected_patterns = moses.WEB_PROTECTED_PATTERNS
        else:
            with open(protected_patterns, encoding="utf8") as fin:
                protected_patterns = [pattern.strip() for pattern in fin.readlines()]
            # Every pattern is compiled and then run over each line, so the file
            # size is a multiplier on the work per line. The operator supplies
            # this file, so this is a guard rail rather than a trust boundary --
            # but an accidental `-p bigfile.txt` should fail fast, not hang.
            if len(protected_patterns) > MAX_PROTECTED_PATTERNS:
                raise click.BadParameter(
                    "%d patterns exceeds the limit of %d"
                    % (len(protected_patterns), MAX_PROTECTED_PATTERNS),
                    param_hint="--protected-patterns",
                )

    moses_tokenize = partial(
        moses.tokenize,
        return_str=True,
        aggressive_dash_splits=aggressive_dash_splits,
        escape=xml_escape,
        protected_patterns=protected_patterns,
    )
    return parallel_or_not(iterator, moses_tokenize, processes, quiet)


########################################################################
# Detokenize
########################################################################


@cli.command("detokenize")
@click.option(
    "--xml-unescape",
    "-x",
    default=True,
    is_flag=True,
    help="Unescape special characters for XML.",
)
@processor
def detokenize_file(
    iterator,
    language,
    processes,
    quiet,
    xml_unescape,
):
    moses = MosesDetokenizer(lang=language)
    moses_detokenize = partial(moses.detokenize, return_str=True, unescape=xml_unescape)
    return parallel_or_not(
        list(map(str.split, iterator)), moses_detokenize, processes, quiet
    )


########################################################################
# Normalize
########################################################################


@cli.command("normalize")
@click.option(
    "--normalize-quote-commas",
    "-q",
    default=True,
    is_flag=True,
    help="Normalize quotations and commas.",
)
@click.option(
    "--normalize-numbers", "-d", default=True, is_flag=True, help="Normalize number."
)
@click.option(
    "--replace-unicode-puncts",
    "-p",
    default=False,
    is_flag=True,
    help="Replace unicode punctuations BEFORE normalization.",
)
@click.option(
    "--remove-control-chars",
    "-c",
    default=False,
    is_flag=True,
    help="Remove control characters AFTER normalization.",
)
@processor
def normalize_file(
    iterator,
    language,
    processes,
    quiet,
    normalize_quote_commas,
    normalize_numbers,
    replace_unicode_puncts,
    remove_control_chars,
):
    moses = MosesPunctNormalizer(
        language,
        norm_quote_commas=normalize_quote_commas,
        norm_numbers=normalize_numbers,
        pre_replace_unicode_punct=replace_unicode_puncts,
        post_remove_control_chars=remove_control_chars,
    )
    moses_normalize = partial(moses.normalize)
    return parallel_or_not(iterator, moses_normalize, processes, quiet)


########################################################################
# Train Truecase
########################################################################


@cli.command("train-truecase")
@click.option(
    "--modelfile", "-m", required=True, help="Filename to save the modelfile."
)
@click.option(
    "--is-asr",
    "-a",
    default=False,
    is_flag=True,
    help="A flag to indicate that model is for ASR.",
)
@click.option(
    "--possibly-use-first-token",
    "-p",
    default=False,
    is_flag=True,
    help="Use the first token as part of truecasing.",
)
@processor
def train_truecaser(
    iterator, language, processes, quiet, modelfile, is_asr, possibly_use_first_token
):
    moses = MosesTruecaser(is_asr=is_asr)
    # `train()` expects `iter(list(str))`, i.e. one list of tokens per sentence,
    # so the raw lines read from stdin have to be split into tokens first.
    # Handing it the unsplit strings makes it iterate them character by
    # character and train a character-level model instead of a word-level one.
    # This matches what `MosesTruecaser.train_from_file()` does with its lines.
    # Materialised as a list so the progress bar keeps a total to count towards.
    moses.train(
        [line.split() for line in iterator],
        possibly_use_first_token=possibly_use_first_token,
        processes=processes,
        progress_bar=(not quiet),
    )
    moses.save_model(modelfile)


########################################################################
# Truecase
########################################################################


@cli.command("truecase")
@click.option(
    "--modelfile", "-m", required=True, help="Filename to save/load the modelfile."
)
@click.option(
    "--is-asr",
    "-a",
    default=False,
    is_flag=True,
    help="A flag to indicate that model is for ASR.",
)
@click.option(
    "--possibly-use-first-token",
    "-p",
    default=False,
    is_flag=True,
    help="Use the first token as part of truecase training.",
)
@processor
def truecase_file(
    iterator, language, processes, quiet, modelfile, is_asr, possibly_use_first_token
):
    # If model file doesn't exists, train a model.
    if not os.path.isfile(modelfile):
        truecaser = MosesTruecaser(is_asr=is_asr)
        # As in `train_truecaser()` above, `train()` needs one list of tokens per
        # sentence rather than the raw lines, otherwise the model comes out
        # character-level. The comprehension also gives training its own copy of
        # the input, leaving `iterator` intact for the truecasing pass below;
        # `process_pipeline()` hands us a list, so it can be walked twice.
        truecaser.train(
            [line.split() for line in iterator],
            possibly_use_first_token=possibly_use_first_token,
            processes=processes,
            progress_bar=(not quiet),
        )
        truecaser.save_model(modelfile)
    # Truecase the file.
    moses = MosesTruecaser(load_from=modelfile, is_asr=is_asr)
    moses_truecase = partial(moses.truecase, return_str=True)
    return parallel_or_not(iterator, moses_truecase, processes, quiet)


########################################################################
# Detruecase
########################################################################


@cli.command("detruecase")
@click.option(
    "--is-headline",
    "-a",
    default=False,
    is_flag=True,
    help="Whether the file are headlines.",
)
@processor
def detruecase_file(iterator, language, processes, quiet, is_headline):
    moses = MosesDetruecaser()
    moses_detruecase = partial(
        moses.detruecase, return_str=True, is_headline=is_headline
    )
    return parallel_or_not(iterator, moses_detruecase, processes, quiet)
