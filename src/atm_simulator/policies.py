from __future__ import annotations

from .domain import ATMState, Customer
from .state import SimulationState


def pick_next_customer_index(state: SimulationState) -> int | None:
    if not state.queue:
        return None
    for idx, customer in enumerate(state.queue):
        if customer.priority_queue_flag:
            return idx
    return 0


def select_available_atm(state: SimulationState) -> int | None:
    for atm_id in sorted(state.atms.keys()):
        if state.atms[atm_id].state == ATMState.IDLE and state.atms[atm_id].cash_available > 0:
            return atm_id
    return None
