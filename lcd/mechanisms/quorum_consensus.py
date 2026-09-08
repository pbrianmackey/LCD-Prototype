"""Majority quorum voting (donor mechanism: social_choice_quorum_voting).

Resolves conflicting reports by which value a majority holds, rather than by
which report carries the latest timestamp.
"""
from collections import Counter


def quorum_resolve(reports):
    """reports: list of (value, timestamp). Returns the majority value, or
    None if no value has strict majority."""
    values = [v for v, _t in reports]
    counts = Counter(values)
    value, count = counts.most_common(1)[0]
    if count > len(reports) / 2:
        return value
    return None
