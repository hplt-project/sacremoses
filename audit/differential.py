"""Differential test: this working tree vs a pristine git revision.

Hardening is only acceptable if it does not change what the library produces.
Unit tests check the cases someone thought of; this checks a large, deliberately
awkward corpus against the *actual previous implementation*, so a behaviour
change cannot hide in a case nobody wrote a test for.

Method: export the pristine revision with ``git archive`` into a temp directory,
run an identical driver under each tree in a separate interpreter (both trees
import as ``sacremoses``, so they cannot share a process), and diff the results.

Every difference must be one of the deliberate fixes listed in EXPECTED_DIFFS
below. Anything else is a regression.

Particular attention is paid to scripts without word delimiters -- Chinese,
Japanese, Thai -- because a whitespace-oriented change can silently destroy
them while every English test still passes.

Usage:

    python3 audit/differential.py            # vs the recorded pristine ref
    python3 audit/differential.py <git-ref>
"""

import json
import os
import subprocess
import sys
import tempfile

#: Upstream hplt-project/sacremoses master, before this audit's changes.
PRISTINE_REF = "53ce2d9"

#: Differences that are intended. Anything outside this set fails the run.
EXPECTED_DIFFS = {
    "is_cjk_boundaries": "range comparison was exclusive; 22 codepoints, incl. U+AC00, were misclassified",
    "perl_parity_leak": "perl_parity=True mutated class attributes, leaking into other instances",
    "protected_sentinel_forgery": "THISISPROTECTED in the input used to be rewritten on restore",
    "protected_token_overflow": "past 1000 spans the placeholder counter overran (assert only, stripped by -O)",
}


def cjk_range_boundaries():
    """The exact codepoints ``is_cjk`` used to get wrong.

    ``is_cjk`` compared ``char < end`` / ``char > start`` against closed
    intervals, so the first and last codepoint of every range fell through --
    22 characters, U+AC00 (GA, the most common Korean syllable) among them.
    """
    # Running this file puts audit/ on sys.path, not the repo root.
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    from sacremoses.util import CJKChars

    boundaries = set()
    for start, end in CJKChars().ranges:
        boundaries.add(chr(start))
        boundaries.add(chr(end))
    return boundaries


def expected_detok_change(key, corpus):
    """True if ``key`` is a detokenisation whose text holds a fixed boundary.

    Derived from the cause rather than hardcoded: the is_cjk fix changes
    whether a space is emitted next to a CJK character, so exactly the corpus
    entries containing a former-boundary codepoint may differ, and only under
    detokenisation. If a change shows up anywhere else, it is a regression.
    """
    if not key.startswith("detok|"):
        return False
    name = key.split("|")[-1]
    text = corpus.get(name, "")
    return any(ch in text for ch in cjk_range_boundaries())

# --------------------------------------------------------------------------
# Corpus. Written as escapes so this file stays ASCII and cannot itself be
# mangled by a mis-encoded checkout -- which is one of the bugs under test.
# --------------------------------------------------------------------------

CORPUS = {
    # --- no word delimiter: the scripts most at risk from a whitespace change
    "zh_raw": "我们今天去北京大学。他说：“你好！”",
    "zh_segmented": "我们 今天 去 北京大学 。",
    "ja_raw": "日本語の文章です。彼は「こんにちは」と言った。",
    "ja_mixed": "Python 3.13 で UTF-8 を使う。",
    "th_raw": "สวัสดีครับ นี่คือภาษาไทย",
    "ko_raw": "가나다 한국어 문장입니다.",
    # U+AC00 and the other exact range boundaries the is_cjk fix touches.
    "ko_boundary": "가 한 一 鿿 ぁ ァ",
    # --- space-delimited: must keep behaving exactly as before
    "en": "This ain't funny. It's actually hillarious, yet double Ls. | [] & You're gonna shake it off? Don't?",
    "en_abbrev": "Dr. Smith went to Washington, D.C. on Jan. 5th at 3 p.m. He paid $4.50 (approx.).",
    "de": "Der Herr Dr. Müller wohnt in Köln, Straße 5. Er sagte: „Guten Tag!“",
    "fr": "L'homme n'est-ce pas déjà arrivé ? « Oui », dit-il.",
    "cs": "Pan Novák přišel pozdě. Žádný problém, řekl.",
    "el": "Ο κ. Παπαδόπουλος είπε· «Καλημέρα».",
    "ru": "Г-н Иванов сказал: «Здравствуйте!»",
    "ar": "قال الدكتور: «مرحبا». هل أنت هنا؟",
    "he": "הוא אמר: שלום!",
    "hi": "डॉ. शर्मा ने कहा। यह ठीक है।",
    # --- punctuation / structure edge cases
    "multidot": "Wait... what?! Really.... Hmm.. yes.",
    "dots_only": "." * 40,
    "urls": "See http://example.com/a/b and mail a.b-c@ex-ample.co.uk now.",
    "xml": '<a href="x">text</a> and <br/> and <b>bold</b>',
    "numbers": "1,234.56 and 1.234,56 and 3.14159 and 007",
    "quotes": "“double” ‘single’ «guill» „deutsch“",
    "dashes": "well-known state-of-the-art re-enter -- em--dash",
    "whitespace": "  leading   and\ttabs\tand   trailing  ",
    "empty": "",
    "single_char": "a",
    "control": "text\x00with\x01control\x02chars",
}

#: Languages whose tokenizer is instantiated per corpus entry.
LANGS = ["en", "de", "fr", "cs", "el", "ru", "zh", "ja", "ko", "th", "ar", "hi"]

# --------------------------------------------------------------------------
# Driver: runs inside each tree, prints JSON on stdout.
# --------------------------------------------------------------------------

DRIVER = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
import sacremoses
from sacremoses import MosesTokenizer, MosesDetokenizer, MosesPunctNormalizer
from sacremoses.util import is_cjk

corpus = json.loads(sys.argv[2])
langs = json.loads(sys.argv[3])
out = {}

for lang in langs:
    try:
        tok = MosesTokenizer(lang=lang)
        det = MosesDetokenizer(lang=lang)
    except Exception as exc:
        out["init:%s" % lang] = "ERROR %s: %s" % (type(exc).__name__, exc)
        continue
    for name, text in corpus.items():
        for label, fn in (("tok", lambda t: tok.tokenize(t)),
                          ("detok", lambda t: det.detokenize(tok.tokenize(t)))):
            key = "%s|%s|%s" % (label, lang, name)
            try:
                out[key] = fn(text)
            except Exception as exc:
                out[key] = "ERROR %s: %s" % (type(exc).__name__, exc)

norm = MosesPunctNormalizer()
for name, text in corpus.items():
    try:
        out["norm|%s" % name] = norm.normalize(text)
    except Exception as exc:
        out["norm|%s" % name] = "ERROR %s: %s" % (type(exc).__name__, exc)

# Escape-hatch probes for the four deliberate fixes.
out["probe|is_cjk_boundaries"] = [
    is_cjk(c) for c in "가ᄀ⺀一힣￿A"
]
tok_en = MosesTokenizer(lang="en")
P = MosesTokenizer.BASIC_PROTECTED_PATTERNS
try:
    out["probe|protected_sentinel_forgery"] = " ".join(
        tok_en.tokenize("http://a.com/p THISISPROTECTED000 http://b.com/p",
                        protected_patterns=P))
except Exception as exc:
    out["probe|protected_sentinel_forgery"] = "ERROR %s" % type(exc).__name__
try:
    urls = " ".join("http://e%d.com/p" % i for i in range(1001))
    got = tok_en.tokenize(urls, protected_patterns=P)
    out["probe|protected_token_overflow"] = "ok:%d" % sum(
        1 for u in urls.split() if u in set(got))
except Exception as exc:
    out["probe|protected_token_overflow"] = "ERROR %s" % type(exc).__name__
before = list(MosesPunctNormalizer.NORMALIZE_UNICODE)
MosesPunctNormalizer(perl_parity=True)
out["probe|perl_parity_leak"] = (
    list(MosesPunctNormalizer.NORMALIZE_UNICODE) == before)

print(json.dumps(out, ensure_ascii=True))
'''


def run_tree(tree, label):
    """Run the driver against ``tree`` and return its parsed output."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            DRIVER,
            tree,
            json.dumps(CORPUS),
            json.dumps(LANGS),
        ],
        capture_output=True,
        text=True,
        cwd=tempfile.gettempdir(),  # never import from the CWD
    )
    if result.returncode != 0:
        raise SystemExit(
            "driver failed under %s (%s):\n%s" % (label, tree, result.stderr)
        )
    return json.loads(result.stdout)


def main(argv):
    ref = argv[1] if len(argv) > 1 else PRISTINE_REF
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    with tempfile.TemporaryDirectory() as tmp:
        pristine = os.path.join(tmp, "pristine")
        os.makedirs(pristine)
        archive = subprocess.run(
            ["git", "archive", ref],
            cwd=here,
            capture_output=True,
        )
        if archive.returncode != 0:
            raise SystemExit("git archive %s failed: %s" % (ref, archive.stderr))
        subprocess.run(["tar", "-x", "-C", pristine], input=archive.stdout, check=True)

        print("pristine ref : %s" % ref)
        print("working tree : %s" % here)
        print()
        old = run_tree(pristine, "pristine")
        new = run_tree(here, "working tree")

    keys = sorted(set(old) | set(new))
    diffs = [k for k in keys if old.get(k, "<missing>") != new.get(k, "<missing>")]

    unexpected = []
    boundary_effects = []
    for key in diffs:
        probe = key[len("probe|"):] if key.startswith("probe|") else None
        if probe in EXPECTED_DIFFS:
            print("EXPECTED  %s" % key)
            print("          %s" % EXPECTED_DIFFS[probe])
            print("          pristine: %r" % (old.get(key),))
            print("          patched : %r" % (new.get(key),))
        elif expected_detok_change(key, CORPUS):
            boundary_effects.append(key)
        else:
            unexpected.append(key)

    if boundary_effects:
        print()
        print(
            "EXPECTED  %d detokenisation changes, all on text containing a CJK"
            % len(boundary_effects)
        )
        print("          range boundary that is_cjk used to misclassify.")
        sample = boundary_effects[0]
        print("          e.g. %s" % sample)
        print("            pristine: %r" % (old.get(sample),))
        print("            patched : %r" % (new.get(sample),))
        affected = sorted({k.split("|")[-1] for k in boundary_effects})
        print("          corpus entries affected: %s" % ", ".join(affected))

    print()
    print("compared %d outputs across %d languages" % (len(keys), len(LANGS)))
    print("identical: %d" % (len(keys) - len(diffs)))
    print("expected differences: %d" % (len(diffs) - len(unexpected)))
    print("UNEXPECTED differences: %d" % len(unexpected))

    for key in unexpected:
        print()
        print("  REGRESSION %s" % key)
        print("    pristine: %r" % (old.get(key, "<missing>"),))
        print("    patched : %r" % (new.get(key, "<missing>"),))

    # Every expected difference must actually have occurred: if a fix silently
    # stopped working, the probe would match pristine again and pass unnoticed.
    missing_fixes = [
        name for name in EXPECTED_DIFFS if "probe|" + name not in diffs
    ]
    if missing_fixes:
        print()
        print("FIXES NOT OBSERVED (silently reverted?): %s" % ", ".join(missing_fixes))

    ok = not unexpected and not missing_fixes
    print()
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
