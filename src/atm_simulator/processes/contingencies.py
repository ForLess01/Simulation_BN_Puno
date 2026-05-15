from __future__ import annotations

import simpy

from ..domain import ATMState, EventType
from ..random import RandomEngine
from ..tracing import Event


def contingencies_process(env: simpy.Environment, ctx: dict):
    cfg = ctx["config"]
    rng: RandomEngine = ctx["rng"]
    state = ctx["state"]
    bus = ctx["event_bus"]

    forced_done = {"failure": False, "maintenance": False, "cashout": False}

    def interrupt_customer_if_busy(atm_id: int) -> None:
        atm = state.atms[atm_id]
        customer_id = atm.current_customer_id
        if customer_id is None:
            return
        customer = state.customers.get(customer_id)
        if customer is None:
            return
        customer.abandoned = True
        customer.served_flag = False
        customer.abandon_reason = "falla_percibida"
        customer.abandon_ts = env.now
        customer.departure_ts = env.now
        bus.emit(
            Event(
                EventType.CUSTOMER_ABANDON.value,
                env.now,
                customer.customer_id,
                {},
                {"queue_len": len(state.queue)},
                {"reason": "falla_percibida", "abandoned": True, "served_flag": False},
            )
        )
        atm.current_customer_id = None

    def force_event(kind: str, atm_id: int) -> None:
        atm = state.atms[atm_id]
        if kind == "failure":
            interrupt_customer_if_busy(atm_id)
            atm.state = ATMState.DOWN_FAILURE
            atm.failure_flag = True
            atm.failure_type = "hardware"
            bus.emit(Event(EventType.ATM_FAILURE.value, env.now, f"ATM-{atm_id}", {}, {"state": atm.state.value}, {"atm_id": atm_id, "cash_available": atm.cash_available}))
        elif kind == "maintenance":
            atm.state = ATMState.DOWN_MAINTENANCE
            atm.maintenance_flag = True
            atm.maintenance_type = "preventivo"
            bus.emit(Event(EventType.ATM_MAINTENANCE_START.value, env.now, f"ATM-{atm_id}", {}, {"state": atm.state.value}, {"atm_id": atm_id, "cash_available": atm.cash_available}))
        elif kind == "cashout":
            atm.state = ATMState.CASHOUT
            atm.cash_available = 0
            bus.emit(Event(EventType.ATM_CASHOUT.value, env.now, f"ATM-{atm_id}", {}, {"state": atm.state.value}, {"atm_id": atm_id, "cash_available": atm.cash_available}))

    while env.now <= cfg.duration_sec:
        progress = env.now / max(cfg.duration_sec, 1)
        if cfg.scenario_id == "S5_falla_1_atm" and not forced_done["failure"] and progress >= 0.20:
            force_event("failure", 1)
            forced_done["failure"] = True
        if cfg.scenario_id == "S7_mantenimiento" and not forced_done["maintenance"] and progress >= 0.25:
            force_event("maintenance", 2)
            forced_done["maintenance"] = True
        if cfg.scenario_id == "S9_critico":
            if not forced_done["failure"] and progress >= 0.15:
                force_event("failure", 1)
                forced_done["failure"] = True
            if not forced_done["cashout"] and progress >= 0.30:
                force_event("cashout", 3)
                forced_done["cashout"] = True
            if not forced_done["maintenance"] and progress >= 0.45:
                force_event("maintenance", 2)
                forced_done["maintenance"] = True

        atm_id = rng.randint(1, cfg.total_atm)
        atm = state.atms[atm_id]
        override_failure = cfg.contingency_overrides.get("failure", 1.0)
        override_maintenance = cfg.contingency_overrides.get("maintenance", 1.0)
        override_cashout = cfg.contingency_overrides.get("cashout", 1.0)

        rate_h = 1 / 120.0
        if rng.bernoulli(cfg.distributions.failure_rate_per_hour * override_failure * rate_h):
            interrupt_customer_if_busy(atm_id)
            atm.state = ATMState.DOWN_FAILURE
            atm.failure_flag = True
            atm.failure_type = "hardware"
            bus.emit(Event(EventType.ATM_FAILURE.value, env.now, f"ATM-{atm_id}", {}, {"state": atm.state.value}, {"atm_id": atm_id, "cash_available": atm.cash_available}))
        elif rng.bernoulli(cfg.distributions.maintenance_rate_per_hour * override_maintenance * rate_h):
            atm.state = ATMState.DOWN_MAINTENANCE
            atm.maintenance_flag = True
            atm.maintenance_type = "preventivo"
            bus.emit(Event(EventType.ATM_MAINTENANCE_START.value, env.now, f"ATM-{atm_id}", {}, {"state": atm.state.value}, {"atm_id": atm_id, "cash_available": atm.cash_available}))
        elif rng.bernoulli(cfg.distributions.cashout_rate_per_hour * override_cashout * rate_h):
            atm.state = ATMState.CASHOUT
            atm.cash_available = 0
            bus.emit(Event(EventType.ATM_CASHOUT.value, env.now, f"ATM-{atm_id}", {}, {"state": atm.state.value}, {"atm_id": atm_id, "cash_available": atm.cash_available}))

        for recover_id, recover_atm in state.atms.items():
            if recover_atm.state in {ATMState.CASHOUT, ATMState.DOWN_FAILURE, ATMState.DOWN_MAINTENANCE} and rng.bernoulli(0.03):
                recover_atm.state = ATMState.IDLE
                recover_atm.failure_flag = False
                recover_atm.maintenance_flag = False
                if recover_atm.cash_available <= 0:
                    recover_atm.cash_available = 25000
                    bus.emit(Event(EventType.CASH_REPLENISHMENT.value, env.now, f"ATM-{recover_id}", {}, {"cash": recover_atm.cash_available}, {"atm_id": recover_id, "cash_available": recover_atm.cash_available}))
                bus.emit(Event(EventType.ATM_RECOVERY.value, env.now, f"ATM-{recover_id}", {}, {"state": recover_atm.state.value}, {"atm_id": recover_id, "cash_available": recover_atm.cash_available}))
        yield env.timeout(30)
