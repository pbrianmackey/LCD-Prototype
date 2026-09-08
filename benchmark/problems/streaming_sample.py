"""
Problem: streaming_sample
Donor mechanism: statistics_reservoir_sampling (cross-domain: statistics)
Same-domain distractor / Baseline A: se_materialize_then_sample

Draw a uniform random sample of k ids from a log source that can only be
iterated once, of a size too large to comfortably materialize. Discriminator
is peak memory used while processing the whole stream, measured with
tracemalloc -- not just correctness (both approaches produce a valid uniform
sample; the difference is whether producing it required holding the entire
input in memory at once).
"""
import sys
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lcd.mechanisms.reservoir_sampling import reservoir_sample
from lcd.mechanisms.naive_baselines import materialize_then_sample

N = 3_000_000
K = 200
MEM_LIMIT_MB = 20.0


def _make_stream():
    return (i for i in range(N))


CARD_ADAPTERS = {
    "statistics_reservoir_sampling": lambda: reservoir_sample,
    "se_materialize_then_sample": lambda: materialize_then_sample,
}


def evaluate(candidate):
    stream = _make_stream()
    tracemalloc.start()
    result = candidate(stream, K, seed=123)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mb = peak / (1024 * 1024)
    valid = (len(result) == K and len(set(result)) == K and all(0 <= x < N for x in result))
    passed = bool(valid and peak_mb <= MEM_LIMIT_MB)
    score = -peak_mb
    detail = f"valid={valid} peak_mem={peak_mb:.2f}MB (limit {MEM_LIMIT_MB}MB), n={N}, k={K}"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
