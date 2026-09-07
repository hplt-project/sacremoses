# sacremoses security audit — 2026-08

Everything needed to re-run and review this audit is in this directory. Nothing
here is imported by the package or shipped in the wheel.

    python3 audit/measure.py                    # self-check the complexity classifier
    python3 audit/attacks.py                    # every attack vs the working tree
    python3 audit/attacks.py --ref 53ce2d9      # the same attacks vs pristine upstream
    python3 audit/differential.py               # output equivalence vs pristine

The last two are the ones that make this reviewable by someone who was not
here. `attacks.py --ref 53ce2d9` runs the identical file against the upstream
revision this audit started from and reports **8 of 9 checks VULNERABLE**; run
against the working tree it reports **0**. `differential.py` proves the fixes
did not change what the library produces.

Baseline revision: `53ce2d9` (hplt-project/sacremoses master).

## Results

    $ python3 audit/attacks.py --ref 53ce2d9        $ python3 audit/attacks.py
    A1  VULNERABLE  CWE-407                         A1  DEFENDED
    A2  VULNERABLE  CWE-407                         A2  DEFENDED
    A3  VULNERABLE  CWE-74                          A3  DEFENDED
    A4  VULNERABLE  CWE-617                         A4  DEFENDED
    A5  VULNERABLE  CWE-22                          A5  DEFENDED
    A6  VULNERABLE  CWE-20                          A6  DEFENDED
    A7  VULNERABLE  CWE-59/732                      A7  DEFENDED
    A8  BENIGN      CWE-1333                        A8  BENIGN
    A9  VULNERABLE  CWE-22 precondition             A9  BENIGN
    9 checks, 8 VULNERABLE                          9 checks, 0 VULNERABLE

## Findings

| ID | Finding | CWE | Measured impact | Fix |
|----|---------|-----|-----------------|-----|
| A1 | `replace_multidots` / `restore_multidots` peel one dot per iteration and re-scan the whole string | 407 | `'.'*16000` → **16.76s**; `'.'*64000` ≈ minutes | Single-pass regex both ways. 16.76s → **0.042s** (~400x); 64k now 0.17s |
| A2 | `has_numeric_only` used `[\s]+` before a literal, so every start position re-scans the whitespace run | 407 | `' '*50000` → **96.5s** | `\s` instead of `[\s]+` — provably equivalent for a boolean. 96.5s → **0.0034s** (~28,000x) |
| A3 | Protected-span placeholder was the constant `THISISPROTECTED`, and input was never checked for it | 74 | Input containing the literal had it rewritten into a protected span — a URL could be **relocated or duplicated** into attacker-chosen positions | Escape the stem past the longest run already present, in one linear pass |
| A4 | `assert len(protected_tokens) <= 1000` was the only bound | 617 | Under `-O`/`PYTHONOPTIMIZE` the assert vanishes and the `zfill(3)` counter overruns: span 1000 collides with span 100 and is **silently lost**. Without `-O`, an uncaught empty `AssertionError` | Real `ValueError`, enforced under `-O` too |
| A5 | `Perluniprops.chars(category)` interpolated its argument into a path | 22 | Arbitrary `.txt` file read, demonstrated | Data is now code — a `dict` lookup that raises `KeyError` |
| A6 | Malformed truecase model raised raw `AttributeError`/`ValueError` from the parser | 20 | A downloaded `.truemodel` is untrusted input | One `ValueError` naming the file and line |
| A7 | `save_model` opened the target `"w"` | 59, 732, 367 | Followed a symlink and **truncated the target**; wrote mode `0644`; raced the CLI's `isfile` check | `O_EXCL|O_NOFOLLOW` temp at `0600` + atomic `os.replace` |
| A8 | Nested quantifiers in `BASIC_PROTECTED_PATTERNS` | 1333 | **Not exploitable** — see below | None needed; pinned so it stays that way |
| A9 | Package read data files at run time | 22 (precondition) | Removed the filesystem from the runtime entirely | 29 char classes + 39 prefix lists generated into Python modules |

Also fixed, found in the same sweep but not attacks:

- **`is_cjk` compared closed ranges exclusively** (`util.py`), dropping the
  first and last codepoint of all 11 CJK ranges — 22 characters, including
  **U+AC00**, the most common Korean syllable. `가` and its immediate
  neighbour `각` detokenized *differently*. All 11 ranges are now consistent.
- **`perl_parity=True` assigned into class attributes** (`normalize.py`), so
  constructing one parity normalizer rewrote the defaults for every other
  normalizer in the process.
- **`open()` without `encoding=`** in `tokenize.py`, `sent_tokenize.py`,
  `subwords.py`. 33 of the 39 bundled prefix lists are non-ASCII; `el`, `cs`,
  `as`, `bn`, `ga`, `gu` are not cp1252-decodable at all (hard error on a
  default Windows locale) and `ca`, `de`, `es`, `et`, `fi`, `fr` decode to
  silent mojibake, which is worse.
- **Dependency floors** (`setup.py`): `joblib>=1.2.0` (CVE-2022-21797,
  critical) and `tqdm>=4.66.3` (CVE-2024-34062) — previously unconstrained.

## What this audit is actually about

Neither real DoS finding is catastrophic backtracking. A1 and A2 are ordinary
**quadratic loops** — the kind that a ReDoS scanner, which looks for nested
quantifiers, walks straight past. Meanwhile the four patterns that *do* have
the classic `(a+)+` shape (A8) turned out to be linear.

So the scanner would have flagged exactly the wrong four things and missed both
real ones. That inversion is the single most useful thing to carry out of here.

## Lessons

**On finding this class of bug**

1. **Measure a doubling curve, not a timestamp.** Run n, 2n, 4n, 8n and look at
   the ratio: ~2x linear, ~4x quadratic, >8x exponential. A single wall-clock
   number cannot separate "slow box" from "O(n²)". Both real findings came from
   ratios.
2. **A nested-quantifier shape is neither necessary nor sufficient.**
   `([\w\-\_]+\.)+` looks lethal but is linear, because `\w` cannot cross the
   `.` that separates the groups — the engine has exactly one way to partition
   the input, so there is nothing to backtrack over. Conversely `[\s]+` before
   a literal has no nesting at all and is quadratic.
3. **`while pattern.search(text): text = pattern.sub(...)` is a red flag.**
   Re-scanning a whole string per removed element is quadratic by construction.
   That one shape produced A1.
4. **Grep for `assert` used as a bound.** `python -O` removes it. An assert
   guarding a buffer, counter or index is a silent-corruption bug waiting for
   someone to set `PYTHONOPTIMIZE=1` in a Dockerfile — which is routine.
5. **Any constant sentinel substituted into user text is forgeable** unless the
   text is checked for it first. Restoring with a blind `str.replace` turns
   that into an injection primitive.
6. **Off-by-one in a range table is a linguistic bug, not just an arithmetic
   one.** `char < end` on a closed interval silently changed how one specific
   Korean syllable was spaced. Test the *boundaries* of every range table.

**On measuring, learned by getting each of these wrong first**

7. **One sample is not a measurement.** On a loaded machine a single timing can
   be several times the true cost. Take the **minimum** of k runs — contention
   only ever adds time, so the smallest sample is closest to the truth.
   One-shot timings here labelled `str.count` as QUADRATIC.
8. **A doubling curve cannot measure an exponential.** Finding a measurable
   size means doubling n, and on a backtracking pattern the next doubling never
   returns — the search for a measurement *is* the denial of service. Use an
   absolute-time test on a hand-sized payload instead: `(a+)+$` on `'a'*26`
   takes 13-35s where a linear pattern takes 0.000003s.
9. **Sub-millisecond ratios are noise.** After a fix, the code is fast, and at
   the old payload sizes every row collapses into the noise band where jitter
   fabricates verdicts. Auto-scale the payload until the base measurement is
   worth comparing.
10. **"Too slow to sample twice" is the opposite of "too fast to measure" — do
    not collapse them.** A budget that truncates a curve to two rows leaves one
    ratio. Refusing to classify one ratio reported the pristine quadratic
    (7.3s → 36.0s, a 4.9x jump) as LINEAR. But trusting one ratio
    unconditionally produced a false positive on fixed code timed in
    milliseconds. The rule that works: the fewer samples, the more absolute
    signal required.
11. **Budget the measurement.** Payload sizes chosen so the *fixed* code is
    measurable make the *vulnerable* code take hours — measuring a quadratic
    means paying for it. Without a wall-clock ceiling the same script cannot
    run against both trees, and running against both trees is the whole point.

**On changing a library safely**

12. **Differential-test against the actual previous implementation**, not
    against your idea of it. Unit tests cover the cases someone thought of;
    `differential.py` compares 704 outputs across 12 languages and would catch
    a change in a case nobody wrote a test for.
13. **Derive expected differences from their cause.** `differential.py`
    computes which corpus entries contain a formerly-misclassified codepoint
    and expects detokenisation changes on exactly those. Hardcoding the keys
    would have hidden a real regression in the same place.
14. **Assert the fix is still working.** The differential fails if an expected
    difference *stops* appearing — otherwise a silently reverted fix looks
    identical to a clean run.
15. **Keep the benign findings.** A8 is linear today and is pinned anyway:
    relax one inner character class and those payloads become exponential. A
    file that records only the hits cannot catch that.
16. **Characterise before rewriting.** The exact multidot semantics (a run of k
    dots becomes `" " + "DOT"*k + "MULTI"`, plus a trailing space when
    something follows) were pinned by test first, then the loop was replaced.
    Fuzzing old against new over 4,000 random dot-heavy strings gave 0
    mismatches.

## Files

| File | What it is |
|------|-----------|
| `measure.py` | Complexity classifier — doubling curves, min-of-k timing, absolute-time test for exponentials. `python3 audit/measure.py` self-checks it against a known linear, quadratic and exponential function. |
| `attacks.py` | All 9 attacks, exploitable and benign, runnable against any git revision. |
| `differential.py` | 704 outputs across 12 languages, working tree vs pristine. |
| `../sacremoses/test/test_security_harness.py` | The CI-enforced subset — same coverage as regression tests, sized to run in seconds. |

`test_security_harness.py` is the version that runs in CI on every commit;
this directory is the version a reviewer runs to check the work.

## Reproducing on a clean machine

    git clone <repo> && cd sacremoses
    python3 -m pip install -e .
    python3 audit/measure.py        # PASS
    python3 audit/attacks.py        # 9 checks, 0 VULNERABLE
    python3 audit/differential.py   # RESULT: PASS
    python3 -m pytest sacremoses/test/ -q

The attack scripts write only to temporary directories and clean up after
themselves. `attacks.py --ref` exports the target revision with `git archive`
into a temp directory and never modifies the checkout.
