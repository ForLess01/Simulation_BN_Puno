from __future__ import annotations

import simpy

from ..domain import EventType
from ..random import RandomEngine, should_abandon
from ..tracing import Event


def abandonment_process(env: simpy.Environment, ctx: dict):
    cfg = ctx["config"]
    rng: RandomEngine = ctx["rng"]
    state = ctx["state"]
    bus = ctx["event_bus"]

    while env.now <= cfg.duration_sec:
        for customer in list(state.queue):
            waiting = env.now - customer.arrival_ts
            if should_abandon(waiting, cfg, rng, ctx["pressure"]["composite"]):
                state.queue.remove(customer)
                customer.abandoned = True
                customer.served_flag = False
                customer.abandon_ts = env.now
                customer.departure_ts = env.now
                customer.abandon_reason = "espera_alta" if waiting >= cfg.distributions.abandonment_threshold_sec else "saturacion"
                bus.emit(
                    Event(
                        EventType.CUSTOMER_ABANDON.value,
                        env.now,
                        customer.customer_id,
                        {},
                        {"queue_len": len(state.queue)},
                        {
                            "reason": customer.abandon_reason,
                            "abandoned": True,
                            "served_flag": False,
                        },
                    )
                )
        yield env.timeout(5)
