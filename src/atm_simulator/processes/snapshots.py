from __future__ import annotations

import simpy

from ..domain import EventType
from ..tracing import Event


def snapshot_process(env: simpy.Environment, ctx: dict):
    cfg = ctx["config"]
    state = ctx["state"]
    bus = ctx["event_bus"]

    while env.now <= cfg.duration_sec:
        counts = state.counts()
        payload = {"queue_length_total": len(state.queue), **counts, "blocked_arrivals_count": state.blocked_arrivals_count}
        bus.emit(Event(EventType.SYSTEM_SNAPSHOT.value, env.now, "SYSTEM", {}, payload, payload))
        yield env.timeout(cfg.snapshot_interval_sec)
