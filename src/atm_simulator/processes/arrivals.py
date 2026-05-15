from __future__ import annotations

import simpy

from ..domain import Customer, EventType
from ..random import RandomEngine, interarrival_sampler
from ..tracing import Event


def arrivals_process(env: simpy.Environment, ctx: dict):
    cfg = ctx["config"]
    rng: RandomEngine = ctx["rng"]
    state = ctx["state"]
    bus = ctx["event_bus"]

    counter = 0
    last_arrival_ts: float | None = None
    while env.now <= cfg.duration_sec:
        is_restricted = ctx["is_restricted_window"](env.now)
        interarrival = 0.0 if last_arrival_ts is None else max(0.0, env.now - last_arrival_ts)
        last_arrival_ts = env.now
        is_priority = ctx["priority_profile_sampler"]()
        counter += 1
        customer = Customer(
            customer_id=f"CUST-{counter:05d}",
            arrival_ts=env.now,
            transaction_type=rng.choice(["retiro", "consulta", "pago", "transferencia", "otros"]),
            interarrival_time_sec=interarrival,
            priority_queue_flag=is_priority,
            adulto_mayor_segment="adulto_mayor_mayor" if is_priority else "",
        )
        state.customers[customer.customer_id] = customer
        if is_restricted:
            customer.blocked_by_closed_hours = True
            customer.abandoned = True
            customer.served_flag = False
            customer.abandon_reason = "horario"
            customer.abandon_ts = env.now
            customer.departure_ts = env.now
            state.blocked_arrivals_count += 1
            bus.emit(
                Event(
                    EventType.CUSTOMER_ARRIVAL.value,
                    env.now,
                    customer.customer_id,
                    {},
                    {"blocked": True},
                    {
                        "interarrival_time_sec": interarrival,
                        "blocked_by_closed_hours": True,
                        "transaction_type": customer.transaction_type,
                        "priority_queue_flag": customer.priority_queue_flag,
                        "adulto_mayor_segment": customer.adulto_mayor_segment,
                        "queue_position_at_arrival": 0,
                    },
                )
            )
        else:
            state.enqueue(customer)
            bus.emit(
                Event(
                    EventType.CUSTOMER_ARRIVAL.value,
                    env.now,
                    customer.customer_id,
                    {},
                    {"queue_len": len(state.queue)},
                    {
                        "interarrival_time_sec": interarrival,
                        "blocked_by_closed_hours": False,
                        "transaction_type": customer.transaction_type,
                        "priority_queue_flag": customer.priority_queue_flag,
                        "adulto_mayor_segment": customer.adulto_mayor_segment,
                        "queue_position_at_arrival": customer.queue_position_at_arrival,
                    },
                )
            )
            bus.emit(Event(EventType.QUEUE_ENTER.value, env.now, customer.customer_id, {}, {"queue_position": customer.queue_position_at_arrival}, {}))
        yield env.timeout(interarrival_sampler(cfg, rng))
