from __future__ import annotations

import simpy

from ..domain import ATMState, EventType
from ..random import RandomEngine, service_sampler
from ..tracing import Event


def service_customer(env: simpy.Environment, ctx: dict, customer, atm_id: int):
    state = ctx["state"]
    cfg = ctx["config"]
    rng: RandomEngine = ctx["rng"]
    bus = ctx["event_bus"]

    atm = state.atms[atm_id]
    before = {"atm_state": atm.state.value, "cash": atm.cash_available}
    atm.state = ATMState.BUSY
    customer.service_start_ts = env.now
    customer.atm_id = atm_id
    atm.current_customer_id = customer.customer_id
    bus.emit(
        Event(
            EventType.SERVICE_START.value,
            env.now,
            customer.customer_id,
            before,
            {"atm_state": atm.state.value},
            {"atm_id": atm_id, "cash_available": atm.cash_available},
        )
    )

    duration = service_sampler(cfg, rng, customer.transaction_type)
    yield env.timeout(duration)

    if customer.abandoned:
        return

    atm.cash_available = max(0.0, atm.cash_available - rng.randint(20, 600))
    customer.service_end_ts = env.now
    customer.departure_ts = env.now
    customer.served_flag = True
    customer.abandoned = False
    atm.current_customer_id = None

    if atm.cash_available <= 0:
        atm.state = ATMState.CASHOUT
        event_type = EventType.ATM_CASHOUT.value
    else:
        atm.state = ATMState.IDLE
        event_type = EventType.SERVICE_END.value

    bus.emit(
        Event(
            event_type,
            env.now,
            customer.customer_id,
            {},
            {"atm_state": atm.state.value},
            {
                "atm_id": atm_id,
                "cash_available": atm.cash_available,
                "served_flag": customer.served_flag,
                "abandoned": customer.abandoned,
            },
        )
    )
