from __future__ import annotations

import simpy

from ..policies import pick_next_customer_index, select_available_atm
from .service import service_customer


def customer_flow_process(env: simpy.Environment, ctx: dict):
    state = ctx["state"]
    while env.now <= ctx["config"].duration_sec:
        atm_id = select_available_atm(state)
        if atm_id is not None and state.queue:
            idx = pick_next_customer_index(state)
            customer = state.queue[idx] if idx is not None else None
            if customer is not None:
                del state.queue[idx]
            if customer is not None:
                env.process(service_customer(env, ctx, customer, atm_id))
        yield env.timeout(1)
