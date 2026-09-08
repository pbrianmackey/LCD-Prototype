"""Auction / congestion-pricing scheduling (donor mechanism: economics_congestion_pricing_aging).

Allocates one unit of shared capacity per tick to the highest effective bid,
where bid = base_value + waiting_time * escalation_rate, bounding worst-case
wait time instead of letting a fixed-priority/value rule starve a requester.
"""


def auction_schedule(arrivals, horizon, escalation_rate=0.5):
    """
    arrivals: list of (arrival_tick, task_id, base_value); exactly one task is
    served per tick, chosen by highest current bid among arrived-and-unserved tasks.
    Returns dict task_id -> served_tick (or None if unserved within horizon).
    """
    pending = []  # (task_id, base_value, arrival_tick)
    served = {}
    idx = 0
    arrivals_sorted = sorted(arrivals, key=lambda a: a[0])
    for t in range(horizon):
        while idx < len(arrivals_sorted) and arrivals_sorted[idx][0] == t:
            _, task_id, base_value = arrivals_sorted[idx]
            pending.append([task_id, base_value, t])
            idx += 1
        if not pending:
            continue
        best_i, best_bid = None, None
        for i, (task_id, base_value, arrival_t) in enumerate(pending):
            bid = base_value + (t - arrival_t) * escalation_rate
            if best_bid is None or bid > best_bid:
                best_bid, best_i = bid, i
        task_id, _, _ = pending.pop(best_i)
        served[task_id] = t
    for task_id, _, _ in pending:
        served.setdefault(task_id, None)
    return served
