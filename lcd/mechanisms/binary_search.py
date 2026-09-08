"""Binary search (same-domain donor mechanism: cs_binary_search).

Used for the naive_sufficient control problem: this is standard,
already-in-the-field CS knowledge, so no cross-domain transfer should be
needed here, and LCD should not be penalized for landing on it.
"""


def binary_search(sorted_list, target):
    lo, hi = 0, len(sorted_list) - 1
    comparisons = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        comparisons += 1
        if sorted_list[mid] == target:
            return mid, comparisons
        elif sorted_list[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1, comparisons
