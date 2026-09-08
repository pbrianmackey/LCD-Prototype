"""Ramp-metering admission control (donor mechanism: transportation_ramp_metering).

Admits at most `service_rate` per tick and queues the rest at the edge,
instead of admitting everything and letting the system itself absorb
(and collapse under) the overload.
"""


class RampMeteringAdmission:
    def __init__(self, service_rate):
        self.service_rate = service_rate
        self.queue = 0

    def tick(self, offered_load):
        self.queue += offered_load
        admitted = min(self.queue, self.service_rate)
        self.queue -= admitted
        return admitted
