# -*- coding: utf-8 -*-

"""
Tests for the sacremoses command line interface
"""

import os
import subprocess
import sys
import tempfile
import unittest

from click.testing import CliRunner

from sacremoses.cli import cli


def model_tokens(filename):
    """
    Reads a truecaser model file and returns the set of surface forms it holds.

    Each line looks like ``cat (2/3) Cat (1)``, so the first whitespace
    delimited field is the most frequent surface form of that token.
    """
    tokens = set()
    with open(filename, encoding="utf8") as fin:
        for line in fin:
            fields = line.split()
            if fields:
                tokens.add(fields[0])
    return tokens


class CliTestCase(unittest.TestCase):
    """Common plumbing: a runner, a scratch directory and a `run()` helper."""

    def setUp(self):
        self.runner = CliRunner()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def path(self, filename):
        return os.path.join(self.tmpdir.name, filename)

    def run_cli(self, args, text=None):
        """
        Invokes the CLI and asserts that it exited cleanly.

        `-q` is always prepended so that the progress bar stays off stderr and
        stdout holds nothing but the processed text.
        """
        result = self.runner.invoke(cli, ["-q"] + args, input=text)
        if result.exception is not None and not isinstance(
            result.exception, SystemExit
        ):
            raise result.exception
        self.assertEqual(result.exit_code, 0, result.output)
        return result.stdout

    def lines(self, args, text):
        return self.run_cli(args, text).splitlines()


class TestCliBasics(CliTestCase):
    def test_help_lists_every_command(self):
        result = self.runner.invoke(cli, ["--help"])
        self.assertEqual(result.exit_code, 0)
        for command in [
            "tokenize",
            "detokenize",
            "normalize",
            "truecase",
            "detruecase",
            "train-truecase",
        ]:
            self.assertIn(command, result.stdout)

    def test_short_help_flag(self):
        # CONTEXT_SETTINGS registers `-h` alongside `--help`.
        self.assertEqual(
            self.runner.invoke(cli, ["-h"]).stdout,
            self.runner.invoke(cli, ["--help"]).stdout,
        )

    def test_every_command_has_help(self):
        for command in [
            "tokenize",
            "detokenize",
            "normalize",
            "truecase",
            "detruecase",
            "train-truecase",
        ]:
            result = self.runner.invoke(cli, [command, "--help"])
            self.assertEqual(result.exit_code, 0, command)
            self.assertIn("Usage:", result.stdout)

    def test_version_option_is_registered(self):
        # Not invoked here: `click.version_option()` reads the installed
        # distribution metadata, which is absent when running from a source
        # checkout, so only its presence in the help is portable.
        self.assertIn("--version", self.runner.invoke(cli, ["--help"]).stdout)

    def test_no_deprecation_warnings_from_click(self):
        """
        `cli.py` used to branch on `click.__version__`, which is deprecated in
        Click 8.3 and removed in Click 9.1. Turning DeprecationWarning into an
        error keeps that from creeping back in.
        """
        process = subprocess.run(
            [sys.executable, "-W", "error::DeprecationWarning", "-m", "sacremoses", "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(
            process.returncode, 0, process.stderr.decode("utf8", "replace")
        )


class TestCliTokenize(CliTestCase):
    def test_tokenize(self):
        self.assertEqual(
            self.lines(["tokenize"], "Hello, World!\n"), ["Hello , World !"]
        )

    def test_tokenize_escapes_xml_by_default(self):
        self.assertEqual(self.lines(["tokenize"], "a & b\n"), ["a &amp; b"])

    def test_tokenize_aggressive_dash_splits(self):
        # The dash is split out and, XML escaping being on, written as `@-@`.
        self.assertEqual(
            self.lines(["tokenize", "-a"], "This is a well-known bug\n"),
            ["This is a well @-@ known bug"],
        )

    def test_tokenize_language_option(self):
        # `-l` belongs to the group, so it comes before the command. French
        # splits after the apostrophe, which XML escaping turns into `&apos;`.
        self.assertEqual(
            self.lines(["-l", "fr", "tokenize"], "L'article est bon.\n"),
            ["L&apos; article est bon ."],
        )

    def test_detokenize(self):
        self.assertEqual(
            self.lines(["detokenize"], "Hello , World !\n"), ["Hello, World!"]
        )

    def test_detokenize_unescapes_xml(self):
        self.assertEqual(self.lines(["detokenize"], "a &amp; b\n"), ["a & b"])

    def test_tokenize_detokenize_roundtrip(self):
        # The group is chained, so both commands run over the one stdin.
        text = "Hello, World! This is a test.\n"
        self.assertEqual(
            self.lines(["tokenize", "detokenize"], text), [text.strip()]
        )

    def test_multiple_lines(self):
        self.assertEqual(
            self.lines(["tokenize"], "Hello, World!\nGoodbye, World!\n"),
            ["Hello , World !", "Goodbye , World !"],
        )

    def test_empty_input(self):
        self.assertEqual(self.lines(["tokenize"], ""), [])


class TestCliProtectedPatterns(CliTestCase):
    TEXT = "Visit http://example.com/a_b?x=1 or email foo@bar.com today.\n"

    def test_unprotected_splits_urls_and_emails(self):
        output = self.run_cli(["tokenize"], self.TEXT)
        self.assertIn("http : / / example.com", output)
        self.assertIn("foo @ bar.com", output)

    def test_basic_protected_patterns(self):
        output = self.run_cli(["tokenize", "-p", ":basic:"], self.TEXT)
        self.assertIn("http://example.com/a_b", output)
        self.assertIn("foo@bar.com", output)

    def test_web_protected_patterns(self):
        # `:web:` also keeps the query string attached to the URL.
        output = self.run_cli(["tokenize", "-p", ":web:"], self.TEXT)
        self.assertIn("http://example.com/a_b?x=1", output)
        self.assertIn("foo@bar.com", output)

    def test_protected_patterns_from_file(self):
        patterns = self.path("patterns.txt")
        with open(patterns, "w", encoding="utf8") as fout:
            fout.write("[A-Z]+_[A-Z]+\n")
        output = self.run_cli(["tokenize", "-p", patterns], "the FOO_BAR flag\n")
        self.assertIn("FOO_BAR", output)


class TestCliNormalize(CliTestCase):
    def test_normalize_collapses_spaces(self):
        self.assertEqual(
            self.lines(["normalize"], "Hello    World\n"), ["Hello World"]
        )

    def test_normalize_replace_unicode_puncts(self):
        output = self.run_cli(["normalize", "-p"], "Hello，World\n")
        self.assertIn(",", output)

    def test_normalize_remove_control_chars(self):
        output = self.run_cli(["normalize", "-c"], "Hello\x00World\n")
        self.assertNotIn("\x00", output)


class TestCliDetruecase(CliTestCase):
    def test_detruecase(self):
        self.assertEqual(
            self.lines(["detruecase"], "the adventures of Sherlock Holmes\n"),
            ["The adventures of Sherlock Holmes"],
        )

    def test_detruecase_headline(self):
        self.assertEqual(
            self.lines(["detruecase", "-a"], "the adventures of Sherlock Holmes\n"),
            ["The Adventures of Sherlock Holmes"],
        )


class TestCliTruecase(CliTestCase):
    # Deliberately free of single letter words, so that any one character entry
    # in the trained model can only be a character level training bug.
    TEXT = (
        "The cat sat on the mat .\n"
        "The dog ran fast .\n"
        "the cat is fluffy .\n"
    )

    def test_train_truecase_model_is_word_level(self):
        """
        Regression test: `MosesTruecaser.train()` takes `list(list(str))`, one
        list of tokens per sentence. The CLI used to hand it the raw lines,
        so `train()` iterated each line character by character and wrote out a
        character level model (`h (3/3)`, `e (3/3)`, ...) instead of a word
        level one.
        """
        modelfile = self.path("word.model")
        self.run_cli(["train-truecase", "-m", modelfile], self.TEXT)
        self.assertTrue(os.path.isfile(modelfile))

        tokens = model_tokens(modelfile)
        self.assertTrue(tokens, "the trained model is empty")
        # Real words are present ...
        for word in ["cat", "sat", "mat", "dog", "ran", "fast", "fluffy"]:
            self.assertIn(word, tokens)
        # ... and no entry is a bare character.
        single_characters = sorted(token for token in tokens if len(token) == 1)
        self.assertEqual(
            single_characters,
            [],
            "model is character level, not word level: %r" % single_characters,
        )

    def test_train_truecase_records_casing_counts(self):
        modelfile = self.path("counts.model")
        self.run_cli(["train-truecase", "-m", modelfile], self.TEXT)
        with open(modelfile, encoding="utf8") as fin:
            entries = dict(line.split(None, 1) for line in fin if line.strip())
        # "cat" occurs twice in a non sentence initial position, both lowercase.
        self.assertEqual(entries["cat"].strip(), "(2/2)")

    def test_train_truecase_possibly_use_first_token(self):
        modelfile = self.path("first.model")
        self.run_cli(["train-truecase", "-m", modelfile, "-p"], self.TEXT)
        self.assertTrue(model_tokens(modelfile))

    def test_train_truecase_is_asr(self):
        modelfile = self.path("asr.model")
        self.run_cli(["train-truecase", "-m", modelfile, "-a"], self.TEXT)
        self.assertIn("cat", model_tokens(modelfile))

    def test_train_truecase_emits_nothing_on_stdout(self):
        modelfile = self.path("quiet.model")
        self.assertEqual(
            self.run_cli(["train-truecase", "-m", modelfile], self.TEXT), ""
        )

    def test_train_truecase_requires_modelfile(self):
        result = self.runner.invoke(cli, ["-q", "train-truecase"], input=self.TEXT)
        self.assertNotEqual(result.exit_code, 0)

    def test_truecase_trains_model_when_missing(self):
        """`truecase` reads stdin twice: once to train, once to truecase."""
        modelfile = self.path("auto.model")
        self.assertFalse(os.path.isfile(modelfile))
        output = self.run_cli(["truecase", "-m", modelfile], self.TEXT)
        self.assertTrue(os.path.isfile(modelfile))
        # The model it trained on the way past is word level too.
        tokens = model_tokens(modelfile)
        self.assertIn("cat", tokens)
        self.assertEqual([token for token in tokens if len(token) == 1], [])
        # And the input still came out the other side, one line per input line.
        self.assertEqual(len(output.splitlines()), len(self.TEXT.splitlines()))

    def test_truecase_with_existing_model(self):
        modelfile = self.path("shared.model")
        self.run_cli(["train-truecase", "-m", modelfile], self.TEXT)
        mtime = os.path.getmtime(modelfile)
        output = self.lines(["truecase", "-m", modelfile], "The cat sat .\n")
        # An existing model is loaded, never retrained over.
        self.assertEqual(os.path.getmtime(modelfile), mtime)
        # "the" is the only casing seen for that token, so it wins.
        self.assertEqual(output, ["the cat sat ."])

    def test_truecase_detruecase_roundtrip(self):
        modelfile = self.path("roundtrip.model")
        self.run_cli(["train-truecase", "-m", modelfile], self.TEXT)
        self.assertEqual(
            self.lines(
                ["truecase", "-m", modelfile, "detruecase"], "The cat sat .\n"
            ),
            ["The cat sat ."],
        )


class TestCliTruecaseLanguages(CliTestCase):
    """
    Truecasing is about case, and Han, Kana and Thai are caseless scripts, so
    the CLI must stay a no-op for them whether or not the input is segmented.

    Splitting lines on whitespace is the right fix for both families: for
    space delimited languages it yields words, and for zh/ja/th the CLI's input
    is expected to be pre-segmented, which is the same contract
    `MosesTruecaser.train_from_file()` already applies to the lines it reads.
    """

    SAMPLES = {
        # tag: (raw unsegmented, pre-segmented)
        "zh": (
            "我爱北京天安门。\n我用Python和iPhone写程序。\n北京是中国的首都。\n",
            "我 爱 北京 天安门 。\n我 用 Python 和 iPhone 写 程序 。\n北京 是 中国 的 首都 。\n",
        ),
        "ja": (
            "私は東京に住んでいます。\n私はPythonでiPhoneのアプリを作ります。\n東京は日本の首都です。\n",
            "私 は 東京 に 住ん で い ます 。\n私 は Python で iPhone の アプリ を 作り ます 。\n東京 は 日本 の 首都 です 。\n",
        ),
        "th": (
            "ฉันรักเมืองไทย\nฉันเขียนโปรแกรมด้วยPythonและiPhone\nกรุงเทพเป็นเมืองหลวงของประเทศไทย\n",
            "ฉัน รัก เมือง ไทย\nฉัน เขียน โปรแกรม ด้วย Python และ iPhone\nกรุงเทพ เป็น เมืองหลวง ของ ประเทศไทย\n",
        ),
    }

    def test_truecase_is_a_noop_for_caseless_scripts(self):
        for tag, (raw, segmented) in self.SAMPLES.items():
            for form, text in [("raw", raw), ("segmented", segmented)]:
                with self.subTest(language=tag, form=form):
                    modelfile = self.path("%s_%s.model" % (tag, form))
                    output = self.run_cli(["truecase", "-m", modelfile], text)
                    self.assertEqual(output, text)

    def test_caseless_tokens_never_enter_the_model(self):
        """
        Han, Kana and Thai are Unicode category Lo, which
        `MosesTruecaser.SKIP_LETTERS_REGEX` (Ll/Lu/Lt only) filters out, so a
        segmented model holds the embedded Latin words and nothing else.
        """
        for tag, (_, segmented) in self.SAMPLES.items():
            with self.subTest(language=tag):
                modelfile = self.path("%s_seg_only.model" % tag)
                self.run_cli(["train-truecase", "-m", modelfile], segmented)
                self.assertEqual(model_tokens(modelfile), {"Python", "iPhone"})

    def test_segmented_model_is_word_level(self):
        """
        Before the fix these models held the single letters of the embedded
        Latin words ('P', 'y', 't', 'h', 'o', 'n', 'i', 'e') rather than the
        words themselves.
        """
        for tag, (_, segmented) in self.SAMPLES.items():
            with self.subTest(language=tag):
                modelfile = self.path("%s_words.model" % tag)
                self.run_cli(["train-truecase", "-m", modelfile], segmented)
                tokens = model_tokens(modelfile)
                self.assertIn("Python", tokens)
                self.assertEqual([token for token in tokens if len(token) == 1], [])

    def test_unsegmented_input_trains_nothing(self):
        """
        Without word boundaries each line is a single sentence initial token,
        which training does not count, so the model is empty. That is the
        honest answer: casing cannot be learnt from unsegmented text. It also
        stays usable, truecasing such input is a no-op.
        """
        for tag, (raw, _) in self.SAMPLES.items():
            with self.subTest(language=tag):
                modelfile = self.path("%s_raw_only.model" % tag)
                self.run_cli(["train-truecase", "-m", modelfile], raw)
                self.assertEqual(model_tokens(modelfile), set())

    def test_space_delimited_language_is_unaffected(self):
        """The English counterpart of the checks above: still word level."""
        modelfile = self.path("en.model")
        self.run_cli(
            ["train-truecase", "-m", modelfile],
            "The cat sat on the mat .\nThe dog ran fast .\n",
        )
        tokens = model_tokens(modelfile)
        self.assertIn("cat", tokens)
        self.assertEqual([token for token in tokens if len(token) == 1], [])


class TestCliPipeline(CliTestCase):
    def test_normalize_then_tokenize(self):
        self.assertEqual(
            self.lines(["normalize", "tokenize"], "Hello    World!\n"),
            ["Hello World !"],
        )

    def test_encoding_option(self):
        # Non ASCII input survives the round trip intact.
        self.assertEqual(
            self.lines(["-e", "utf8", "tokenize"], "café, s'il vous plaît\n"),
            ["café , s &apos;il vous plaît"],
        )

    def test_processes_option(self):
        self.assertEqual(
            self.lines(["-j", "2", "tokenize"], "Hello, World!\n"),
            ["Hello , World !"],
        )


if __name__ == "__main__":
    unittest.main()
