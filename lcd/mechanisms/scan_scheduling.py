"""SCAN / elevator scheduling (donor mechanism: logistics_elevator_scan).

Sweeps monotonically in the current direction servicing every pending request
in path, then reverses, instead of always chasing the nearest request.
"""


class ScanPolicy:
    """Incremental / real-time version: requests can keep arriving. Commits to
    a sweep direction and continues serving every pending request in that
    direction before reversing, rather than re-evaluating 'nearest' after
    every single stop."""

    def __init__(self, initial_direction=1):
        self.direction = initial_direction

    def next_target(self, pending, pos):
        if not pending:
            return None
        if self.direction >= 0:
            ahead = [r for r in pending if r >= pos]
            if ahead:
                return min(ahead)
            self.direction = -1
            return max(pending)
        else:
            behind = [r for r in pending if r <= pos]
            if behind:
                return max(behind)
            self.direction = 1
            return min(pending)


def scan_schedule(requests, start, initial_direction=1):
    reqs = sorted(set(requests))
    up = sorted([r for r in reqs if r >= start])
    down = sorted([r for r in reqs if r < start], reverse=True)
    if initial_direction >= 0:
        order = up + down
    else:
        order = down + up
    pos = start
    dist = 0
    for r in order:
        dist += abs(r - pos)
        pos = r
    return order, dist
