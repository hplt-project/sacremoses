"""Every attack considered in this audit, exploitable or not.

The point of keeping the benign ones is that "we looked at this and it was
fine" is only useful if a third party can re-run it. A payload that measures
linear today becomes an attack the moment someone relaxes a character class,
and a file that records only the hits cannot catch that.

Each check runs against whichever tree is on ``sys.path``, so the same file
demonstrates the vulnerability on the pristine revision and the fix on the
current one:

    python3 audit/attacks.py                 # current working tree
    python3 audit/attacks.py --ref 53ce2d9   # pristine: several will report VULNERABLE

Exit status is 0 only when every check reports DEFENDED or BENIGN.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

VULNERABLE = "VULNERABLE"
DEFENDED = "DEFENDED"
BENIGN = "BENIGN"  # audited, never exploitable, pinned so it stays that way

CHECKS = []


def check(ident, title, cwe):
    """Register an attack. The function returns ``(status, evidence)``."""

    def register(func):
        CHECKS.append((ident, title, cwe, func))
        return func

    return register


# ==========================================================================
# A1/A2 -- algorithmic complexity. Neither is catastrophic backtracking.
# ==========================================================================


@check("A1", "Multidot run is quadratic in tokenize()", "CWE-407")
def a1_multidot():
    from measure import QUADRATIC, classify, doubling_curve

    from sacremoses import MosesTokenizer

    moses = MosesTokenizer()
    rows = doubling_curve(moses.tokenize, lambda n: "." * n, start=1000, doublings=4)
    verdict, median = classify(rows)
    evidence = "  ".join("n=%d %.3fs" % (n, s) for n, s, _ in rows)
    status = VULNERABLE if verdict == QUADRATIC else DEFENDED
    return status, "%s (median %.1fx/doubling)  %s" % (verdict, median, evidence)


@check("A2", "has_numeric_only is quadratic on a whitespace flood", "CWE-407")
def a2_numeric_only():
    from measure import QUADRATIC, classify, doubling_curve

    from sacremoses import MosesTokenizer

    moses = MosesTokenizer()
    rows = doubling_curve(
        moses.has_numeric_only, lambda n: " " * n + "x", start=12500, doublings=4
    )
    verdict, median = classify(rows)
    evidence = "  ".join("n=%d %.3fs" % (n, s) for n, s, _ in rows)
    status = VULNERABLE if verdict == QUADRATIC else DEFENDED
    return status, "%s (median %.1fx/doubling)  %s" % (verdict, median, evidence)


# ==========================================================================
# A3/A4 -- integrity of the protected-span mechanism.
# ==========================================================================


@check("A3", "Placeholder sentinel is forgeable from input text", "CWE-74")
def a3_sentinel_forgery():
    from sacremoses import MosesTokenizer

    moses = MosesTokenizer()
    patterns = MosesTokenizer.BASIC_PROTECTED_PATTERNS
    text = "http://a.com/p THISISPROTECTED000 http://b.com/p"
    out = " ".join(moses.tokenize(text, protected_patterns=patterns))
    forged = "THISISPROTECTED000" not in out or out.count("http://a.com/p") > 1
    return (
        VULNERABLE if forged else DEFENDED,
        "input %r -> %r" % (text, out),
    )


@check("A4", "Placeholder counter overruns past 1000 spans under -O", "CWE-617")
def a4_placeholder_overrun():
    # Must run in a child interpreter: -O is decided at startup.
    program = (
        "from sacremoses import MosesTokenizer as T\n"
        "m = T(); P = T.BASIC_PROTECTED_PATTERNS\n"
        "urls = ['http://e%d.com/p' % i for i in range(1001)]\n"
        "try:\n"
        "    out = set(m.tokenize(' '.join(urls), protected_patterns=P))\n"
        "except (ValueError, AssertionError) as exc:\n"
        "    print('BOUNDED', type(exc).__name__)\n"
        "else:\n"
        "    print('LOST', sum(1 for u in urls if u not in out))\n"
    )
    result = subprocess.run(
        [sys.executable, "-O", "-c", program],
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path)),
    )
    output = (result.stdout + result.stderr).strip()
    if output.startswith("BOUNDED ValueError"):
        return DEFENDED, "python -O: %s" % output
    return VULNERABLE, "python -O: %s" % output


# ==========================================================================
# A5 -- path traversal through a data lookup.
# ==========================================================================


@check("A5", "Traversal via Perluniprops category name", "CWE-22")
def a5_traversal():
    from sacremoses.corpus import Perluniprops

    secret = None
    try:
        handle, secret = tempfile.mkstemp(suffix=".txt")
        os.write(handle, b"TOP-SECRET-CONTENTS")
        os.close(handle)
        # Depth from the package data directory back up to the temp file.
        import sacremoses

        pkgdir = os.path.dirname(os.path.abspath(sacremoses.__file__))
        datadir = os.path.join(pkgdir, "data", "perluniprops")
        depth = len(os.path.relpath(datadir, "/").split(os.sep))
        payload = "../" * depth + os.path.relpath(secret, "/")[: -len(".txt")]
        try:
            content = "".join(Perluniprops().chars(payload))
        except (KeyError, OSError, ValueError) as exc:
            return DEFENDED, "%s -> %s" % (type(exc).__name__, str(exc)[:60])
        if "TOP-SECRET" in content:
            return VULNERABLE, "read %r via %r" % (content[:24], payload[:36])
        return DEFENDED, "no traversal (returned %d chars)" % len(content)
    finally:
        if secret and os.path.exists(secret):
            os.unlink(secret)


# ==========================================================================
# A6/A7 -- the truecase model file is a trust boundary.
# ==========================================================================


@check("A6", "Malformed truecase model raises an unhandled exception", "CWE-20")
def a6_model_parse():
    from sacremoses import MosesTruecaser

    tmp = tempfile.mkdtemp()
    try:
        results = []
        for name, content in [
            ("odd_fields", "The (5/7) extra\n"),
            ("non_integer", "The (a/7)\n"),
            ("float_count", "The (5.5/7)\n"),
        ]:
            path = os.path.join(tmp, name)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(content)
            try:
                MosesTruecaser(load_from=path)
                results.append("%s: NO ERROR" % name)
            except ValueError:
                results.append("%s: ValueError" % name)
            except Exception as exc:
                results.append("%s: %s" % (name, type(exc).__name__))
        # ValueError is the contract; anything else leaked from the parser.
        bad = [r for r in results if not r.endswith("ValueError")]
        return (
            VULNERABLE if bad else DEFENDED,
            ", ".join(results),
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@check("A7", "save_model follows a symlink and writes world-readable", "CWE-59/732")
def a7_symlink_write():
    import stat

    from sacremoses import MosesTruecaser

    tmp = tempfile.mkdtemp()
    try:
        victim = os.path.join(tmp, "victim.txt")
        with open(victim, "w", encoding="utf-8") as handle:
            handle.write("PRECIOUS")
        link = os.path.join(tmp, "link")
        os.symlink(victim, link)

        truecaser = MosesTruecaser()
        truecaser.train([["The", "cat", "sat", "."]])
        truecaser.save_model(link)

        with open(victim, encoding="utf-8") as handle:
            survived = handle.read() == "PRECIOUS"
        mode = stat.S_IMODE(os.stat(link).st_mode)
        world_readable = bool(mode & (stat.S_IRGRP | stat.S_IROTH))
        if not survived:
            return VULNERABLE, "symlink followed: victim truncated (mode %o)" % mode
        if world_readable:
            return VULNERABLE, "victim intact but model is mode %o" % mode
        return DEFENDED, "victim intact, model mode %o" % mode
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
# A8 -- BENIGN. Kept because the shape is the dangerous one.
# ==========================================================================


@check("A8", "Nested quantifiers in BASIC_PROTECTED_PATTERNS", "CWE-1333")
def a8_protected_pattern_redos():
    from measure import blows_up

    from sacremoses import MosesTokenizer

    # Each payload drives the pattern's inner group hard, then denies the tail
    # the literal it needs, which is what forces backtracking.
    payloads = {
        # ([\w\-\_]+\.)+ then needs [a-zA-Z]{2,}: a digit denies it.
        "PATTERN_4": lambda n: "a@" + "a." * n + "1",
        # (\/\w+)* then needs \/[\w\-\.]+ : a bare trailing slash denies it.
        "PATTERN_5": lambda n: "http://a" + "/a" * n + "/",
        # ( [a-zA-Z0-9]+="?[^"]")+ then needs '>': no '>' denies it.
        "PATTERN_2": lambda n: "<a" + ' a="b"' * n + " ",
        "PATTERN_3": lambda n: "<a" + " a='b'" * n + " ",
    }
    # Absolute-time test, not a doubling curve: a curve needs two comparable
    # measurements and on a truly exponential pattern the second one never
    # arrives (see measure.blows_up). n=40 repetitions is microseconds for a
    # pattern that cannot backtrack and unreachable for one that can.
    timings = []
    for name, make in payloads.items():
        attribute = "BASIC_PROTECTED_PATTERN_" + name.rsplit("_", 1)[1]
        pattern = re.compile(getattr(MosesTokenizer, attribute), re.IGNORECASE)
        exceeded, seconds = blows_up(pattern.search, make(40), budget=1.0)
        timings.append("%s=%.4fs" % (name, seconds))
        if exceeded:
            return VULNERABLE, "%s took %.2fs on 40 repetitions" % (name, seconds)
    # All fast because every inner group is delimiter-anchored: \w+ cannot
    # cross '.', '/' or '"', so the engine has exactly one way to partition the
    # input and there is nothing to backtrack over. The SHAPE is still the
    # classic catastrophic one, which is why this stays pinned: relax an inner
    # character class and these payloads become exponential.
    return BENIGN, "all fast (inner groups delimiter-anchored): " + " ".join(timings)


# ==========================================================================
# A9 -- BENIGN. Recorded so a future change cannot reintroduce file loading.
# ==========================================================================


@check("A9", "Runtime file loading in the package", "CWE-22 precondition")
def a9_no_file_loading():
    import sacremoses.corpus as corpus

    with open(corpus.__file__, encoding="utf-8") as handle:
        source = handle.read()
    found = [t for t in ("open(", "pkgutil", "__file__", "os.path") if t in source]
    if found:
        return VULNERABLE, "corpus.py still references: %s" % ", ".join(found)
    return BENIGN, "corpus.py performs no filesystem access"


# ==========================================================================


def run(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref",
        help="run against this git revision instead of the working tree "
        "(use 53ce2d9 to see the pre-audit behaviour)",
    )
    args = parser.parse_args(argv)

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)

    if args.ref:
        # Re-exec against an exported copy of that revision.
        tmp = tempfile.mkdtemp()
        try:
            archive = subprocess.run(
                ["git", "archive", args.ref], cwd=root, capture_output=True
            )
            if archive.returncode != 0:
                raise SystemExit("git archive %s failed" % args.ref)
            subprocess.run(["tar", "-x", "-C", tmp], input=archive.stdout, check=True)
            # audit/ is not in old revisions; copy this harness across.
            shutil.copytree(here, os.path.join(tmp, "audit"), dirs_exist_ok=True)
            print("running against git revision %s\n" % args.ref)
            return subprocess.run(
                [sys.executable, os.path.join(tmp, "audit", "attacks.py")],
                cwd=tmp,
            ).returncode
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    sys.path.insert(0, root)
    sys.path.insert(0, here)  # for `measure`

    print("tree: %s\n" % root)
    failures = 0
    for ident, title, cwe, func in CHECKS:
        try:
            status, evidence = func()
        except Exception as exc:  # an attack that crashes is still a finding
            status, evidence = VULNERABLE, "%s: %s" % (type(exc).__name__, exc)
        if status == VULNERABLE:
            failures += 1
        print("%-4s %-11s %-9s %s" % (ident, status, cwe, title))
        print("     %s" % evidence)
    print()
    print("%d checks, %d VULNERABLE" % (len(CHECKS), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
