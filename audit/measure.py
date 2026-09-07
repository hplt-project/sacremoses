"""Complexity measurement helpers shared by the attack scripts.

The single most useful tool in this audit was not a scanner. It was a doubling
curve: run the same code on n, 2n, 4n, 8n and look at the ratio between
successive timings.

    ratio ~ 2   linear
    ratio ~ 4   quadratic
    ratio > 8   exponential (catastrophic backtracking)

A single wall-clock number cannot distinguish "this box is loaded" from "this
is O(n**2)", and it is the ratio -- not the absolute time -- that says whether
an input is an attack. Both real findings in this audit were found this way,
and neither is catastrophic backtracking: they are ordinary quadratic loops
(CWE-407) that every ReDoS-shaped scanner walks straight past.

Usage:

    python3 audit/measure.py

Runs the built-in self-check, which asserts the classifier labels a known
linear, a known quadratic and a known exponential function correctly.
"""

import re
import time

LINEAR = "LINEAR"
QUADRATIC = "QUADRATIC"
EXPONENTIAL = "EXPONENTIAL"


#: Repetitions to take the minimum over. One sample is not a measurement: on a
#: loaded machine a single timing can be several times the true cost, and this
#: harness was written on a box running eleven concurrent jobs, where one-shot
#: timings labelled ``str.count`` -- perfectly linear -- as QUADRATIC.
#: Minimum-of-k is the robust estimator because contention can only ever ADD
#: time, never remove it, so the smallest sample is the closest to the truth.
TIMING_REPEATS = 3

#: Above this, one run is already long enough that scheduler noise is a small
#: fraction of it, and repeating would triple an already expensive measurement.
CHEAP_ENOUGH_TO_REPEAT = 0.5


def timed(func, *args, repeats=TIMING_REPEATS):
    """Return the wall-clock seconds one call to ``func`` takes.

    Reports the fastest of ``repeats`` runs -- see TIMING_REPEATS for why the
    minimum rather than the mean. Long calls are measured once.
    """
    best = None
    for _ in range(repeats):
        start = time.perf_counter()
        func(*args)
        elapsed = time.perf_counter() - start
        best = elapsed if best is None else min(best, elapsed)
        if elapsed > CHEAP_ENOUGH_TO_REPEAT:
            break
    return best


#: A measurement below this is dominated by timer and interpreter noise, and
#: its ratio to the next one says nothing about complexity. Learned the hard
#: way: a curve of 1ms/22ms/3ms/17ms is not quadratic, it is jitter, and at a
#: 0.1ms floor the classifier confidently called it QUADRATIC.
NOISE_FLOOR = 0.005

#: Never grow a payload past this while auto-scaling. An exponential function
#: crosses the target time almost immediately, so this only bounds the linear
#: ones, and it keeps the harness from allocating unbounded strings.
MAX_AUTOSCALE = 4_000_000


#: A lone ratio is trusted only when the slower of its two measurements is at
#: least this long. Twenty times the noise floor: enough that jitter cannot
#: manufacture a 3x jump, low enough that a genuinely quadratic path -- which
#: reaches seconds fast -- always clears it.
CONFIDENT_FLOOR = 0.1

#: Wall-clock ceiling for one curve. Without it the same script cannot run on
#: both trees: sizes chosen so the *fixed* code is measurable make the
#: *vulnerable* code take hours -- measuring the quadratic means paying for it.
#: Stop once there is enough signal, and classify on the rows collected.
CURVE_BUDGET = 30.0


def doubling_curve(
    func,
    make_payload,
    start=1000,
    doublings=4,
    warmup=True,
    autoscale=True,
    budget=CURVE_BUDGET,
):
    """Time ``func(make_payload(n))`` for n, 2n, 4n ... and return the rows.

    Each row is ``(n, seconds, ratio_to_previous_or_None)``.

    With ``autoscale`` the starting size is doubled until the base measurement
    clears NOISE_FLOOR, so the ratios compare real work rather than jitter.
    That matters most for the code that has already been fixed: once a
    quadratic becomes linear it also becomes fast, and at the old fixed sizes
    every row collapsed into the noise band.

    Pass ``autoscale=False`` for a payload that may be EXPONENTIAL. Auto-scaling
    doubles the input to find a measurable size, and on an exponential function
    the very next doubling does not return -- the search for a good measurement
    becomes the denial of service. Those payloads must be hand-sized.
    """
    if warmup:
        # Pay for regex compilation and any import-time work once, up front, so
        # it is not charged to the first (smallest, most ratio-sensitive) row.
        func(make_payload(start))

    size = start
    spent = 0.0
    if autoscale:
        # Grow only while the work is too small to measure. On vulnerable code
        # the first size is already slow, so this loop does nothing -- which is
        # what lets one script serve both trees.
        while True:
            elapsed = timed(func, make_payload(size))
            spent += elapsed
            if elapsed >= NOISE_FLOOR or size * 2 > MAX_AUTOSCALE or spent > budget:
                break
            size *= 2

    rows = []
    previous = None
    for _ in range(doublings):
        seconds = timed(func, make_payload(size))
        rows.append((size, seconds, None if previous is None else seconds / previous))
        previous = seconds
        size *= 2
        spent += seconds
        # Two rows is the minimum for a ratio; past the budget, stop paying.
        if spent > budget and len(rows) >= 2:
            break
    return rows


def classify(rows, floor=NOISE_FLOOR):
    """Label a doubling curve LINEAR / QUADRATIC / EXPONENTIAL.

    Uses the median ratio, so one noisy sample cannot flip the verdict. Rows
    faster than ``floor`` are dropped as noise.

    If *no* row clears the floor the function is too fast at this size to be an
    attack, and LINEAR is the honest answer. But a single surviving ratio is
    NOT that case and must still be classified: when the code under test is
    slow, the curve budget stops after two rows, so one ratio is all there is.
    An earlier version required two ratios and therefore reported the pristine
    quadratic -- 7.3s then 36.0s, a 4.9x jump -- as LINEAR. Too slow to sample
    twice is the opposite of too fast to measure; do not collapse them.

    The catch is that one ratio has no median to protect it, so a single noisy
    sample flips the verdict -- which promptly produced a false QUADRATIC on
    already-fixed code timed in tens of milliseconds. Hence the rule: the fewer
    samples, the more absolute signal required. A lone ratio counts only when
    the slower measurement is well clear of the noise band (CONFIDENT_FLOOR);
    otherwise wait for a second ratio.
    """
    usable = [
        (seconds, ratio)
        for _, seconds, ratio in rows
        if ratio is not None and seconds > floor
    ]
    if not usable:
        return LINEAR, 0.0
    if len(usable) == 1 and usable[0][0] < CONFIDENT_FLOOR:
        return LINEAR, 0.0
    ratios = sorted(ratio for _, ratio in usable)
    median = ratios[len(ratios) // 2]
    if median >= 6.0:
        return EXPONENTIAL, median
    if median >= 3.0:
        return QUADRATIC, median
    return LINEAR, median


def blows_up(func, payload, budget=1.0):
    """Absolute-time test: does one hand-sized payload exceed ``budget``?

    This -- not the doubling curve -- is the right tool for catastrophic
    backtracking. A curve needs at least two comparable measurements, and for
    an exponential function the second one never arrives: doubling n from 20
    to 40 turns a one-second match into a longer-than-the-universe match.
    Measuring the blow-up *is* triggering it.

    So exponential payloads are hand-sized instead: pick an n where a linear
    engine finishes in microseconds, and treat "still running after a second"
    as the finding. Returns ``(exceeded, seconds)``.
    """
    seconds = timed(func, payload)
    return seconds > budget, seconds


def report(title, func, make_payload, start=1000, doublings=4, autoscale=True):
    """Measure, print the curve, and return ``(verdict, median_ratio)``."""
    rows = doubling_curve(
        func, make_payload, start=start, doublings=doublings, autoscale=autoscale
    )
    verdict, median = classify(rows)
    print("%s -> %s (median ratio %.2fx)" % (title, verdict, median))
    for size, seconds, ratio in rows:
        suffix = "" if ratio is None else "  (%.1fx)" % ratio
        print("    n=%-8d %9.4fs%s" % (size, seconds, suffix))
    return verdict, median


def _self_check():
    """The classifier has to be trustworthy before any verdict below is."""
    linear = lambda s: s.count("a")
    quadratic = lambda s: sum(len(s[i:]) for i in range(0, len(s), 1000))
    backtrack = re.compile(r"(a+)+$").match

    ok = True
    for title, func, make, start, expected in [
        ("known linear   ", linear, lambda n: "a" * n, 20000, LINEAR),
        ("known quadratic", quadratic, lambda n: "a" * n, 20000, QUADRATIC),
    ]:
        verdict, _ = report(title, func, make, start=start)
        if verdict != expected:
            print("    !! expected %s" % expected)
            ok = False
        print()

    # Catastrophic backtracking is checked by absolute time, not by a curve --
    # see blows_up(). n=26 is microseconds for any non-backtracking engine.
    exceeded, seconds = blows_up(backtrack, "a" * 26 + "!", budget=1.0)
    print("known exponential -> (a+)+$ on 'a'*26 + '!' took %.2fs" % seconds)
    if not exceeded:
        print("    !! expected it to exceed the 1.0s budget")
        ok = False
    # And the counterpart: the same payload against a linear pattern.
    _, fast = blows_up(re.compile(r"a+$").match, "a" * 26 + "!", budget=1.0)
    print("known linear regex -> a+$ on the same payload took %.6fs" % fast)
    if fast > 0.01:
        print("    !! a non-backtracking pattern should be microseconds")
        ok = False

    print()
    print("classifier self-check:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_self_check())
