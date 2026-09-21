import os
import tempfile
import unittest

from sacremoses import MosesTruecaser


class TestTruecaseModel(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.filename = os.path.join(self.tmpdir.name, "model")

    def load_text(self, text):
        with open(self.filename, "w", encoding="utf8") as fout:
            fout.write(text)
        return MosesTruecaser(self.filename)

    def test_fractional_training_roundtrip(self):
        for is_asr in (False, True):
            with self.subTest(is_asr=is_asr):
                original = MosesTruecaser(is_asr=is_asr)
                original.train(
                    [["(", "Hello"], ["hello"], ["start", "Hello"]],
                    possibly_use_first_token=True,
                    save_to=self.filename,
                )
                restored = MosesTruecaser(self.filename, is_asr=is_asr)
                self.assertEqual(restored.model, original.model)
                self.assertEqual(
                    restored.truecase("HELLO hello", use_known=True),
                    original.truecase("HELLO hello", use_known=True),
                )
                restored.save_model(self.filename)
                self.assertEqual(
                    MosesTruecaser(self.filename, is_asr=is_asr).model,
                    original.model,
                )

    def test_fractional_counts_are_sorted_numerically(self):
        model = self.load_text("Hello (0.9/2.0) HELLO (1.1)\n")
        self.assertEqual(model.model["best"]["hello"], "HELLO")
        self.assertEqual(model.model["casing"]["hello"]["Hello"], 0.9)

    def test_large_integer_counts_remain_exact(self):
        model = self.load_text(
            "Hello (9007199254740992/18014398509481985) "
            "HELLO (9007199254740993)\n"
        )
        self.assertEqual(model.model["best"]["hello"], "HELLO")
        self.assertEqual(
            model.model["casing"]["hello"]["HELLO"], 9007199254740993
        )
        self.assertIsInstance(model.model["casing"]["hello"]["HELLO"], int)

    def test_malformed_and_nonfinite_counts_are_rejected(self):
        for count in ("invalid", "nan", "inf", "-inf", "1e999"):
            with self.subTest(count=count):
                with self.assertRaisesRegex(ValueError, "malformed truecase model.*line 1"):
                    self.load_text("Hello (%s/1)\n" % count)

    def test_incomplete_pair_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "odd number of fields"):
            self.load_text("Hello\n")
