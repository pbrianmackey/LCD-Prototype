"""
Problem: impossible_sort_probe   [control_type = no_kb_solution]
Donor mechanism: none -- nothing in the knowledge base solves this.
Baseline A: cs_binary_search (present only so a baseline_a_card_id exists; it
is not expected to pass either).

Sort 50 arbitrary distinct comparable items using at most n=50 comparisons
in total. This is impossible for any correct comparison-based sort: n
comparisons distinguish at most 2^n orderings, but there are n! possible
permutations, and 2^50 << 50!. No amount of cleverness in *which* comparisons
to make escapes the bound (the true lower bound is about n*log2(n) - 1.44n).

Nothing in this prototype's 40-card knowledge base is a sorting algorithm.
The two adapters wired up here are the most plausible near-misses a
retriever might surface (binary search, linear scan) applied as sensibly as
possible to a sorting task -- binary insertion sort and selection sort via
repeated linear scan. Both really do sort correctly. Both still need far
more than n comparisons, because neither escapes the fundamental
information-theoretic bound. This is the intended, correct outcome: every
attempt should fail, and the system should report "no solution found"
rather than a false positive.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import random

from lcd.mechanisms.binary_search import binary_search
from lcd.mechanisms.naive_baselines import linear_scan

N = 50
MAX_COMPARISONS = N  # the impossible budget


def _items():
    rng = random.Random(9)
    items = list(range(N * 10))
    rng.shuffle(items)
    return items[:N]


def _binary_insertion_sort():
    def solve():
        items = _items()
        result = []
        comparisons = 0
        for x in items:
            lo, hi = 0, len(result)
            while lo < hi:
                mid = (lo + hi) // 2
                comparisons += 1
                if result[mid] < x:
                    lo = mid + 1
                else:
                    hi = mid
            result.insert(lo, x)
        return result, comparisons
    return solve


def _selection_sort_via_linear_scan():
    def solve():
        items = _items()[:]
        result = []
        comparisons = 0
        while items:
            best_i = 0
            for i in range(1, len(items)):
                comparisons += 1
                if items[i] < items[best_i]:
                    best_i = i
            result.append(items.pop(best_i))
        return result, comparisons
    return solve


CARD_ADAPTERS = {
    "cs_binary_search": _binary_insertion_sort,
    "se_linear_scan": _selection_sort_via_linear_scan,
}


def evaluate(candidate):
    result, comparisons = candidate()
    correctly_sorted = result == sorted(result) and sorted(result) == sorted(_items())
    passed = bool(correctly_sorted and comparisons <= MAX_COMPARISONS)
    score = -comparisons
    detail = f"comparisons={comparisons} (impossible budget <= {MAX_COMPARISONS}), correctly_sorted={correctly_sorted}"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
