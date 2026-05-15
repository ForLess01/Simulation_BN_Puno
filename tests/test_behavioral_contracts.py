from __future__ import annotations

from datetime import datetime

import pandas as pd
import simpy

from atm_simulator.config import ScenarioConfig
from atm_simulator.domain import ATM, ATMState, Customer
from atm_simulator.processes.customer_flow import customer_flow_process
from atm_simulator.runner import run_scenario
from atm_simulator.state import SimulationState
from atm_simulator.tracing import EventBus


def test_atomic_state_transition_consistency(tmp_path):
    cfg = ScenarioConfig("S1_normal", seed=909, duration_sec=600)
    cfg.output_root = tmp_path
    cfg.distributions.failure_rate_per_hour = 0.0
    cfg.distributions.maintenance_rate_per_hour = 0.0
    cfg.distributions.cashout_rate_per_hour = 0.0

    result = run_scenario(cfg)
    customer = pd.read_csv(result.customer_log)
    atm = pd.read_csv(result.atm_log)

    busy_rows = atm[atm["atm_state"] == "busy"].copy()
    busy_rows["start"] = pd.to_datetime(busy_rows["state_start_ts"])
    busy_rows["end"] = pd.to_datetime(busy_rows["state_end_ts"])
    assert (busy_rows["end"] >= busy_rows["start"]).all()

    served = customer[(customer["served_flag"] == True) & (customer["atm_id"].notna())].copy()
    served["service_start"] = pd.to_datetime(served["service_start_ts"], errors="coerce")

    # Atomicity contract: every service_start is covered by one busy ATM interval
    for _, row in served.head(30).iterrows():
        atm_id = int(row["atm_id"])
        service_start = row["service_start"]
        in_busy_interval = busy_rows[
            (busy_rows["atm_id"] == atm_id)
            & (busy_rows["start"] <= service_start)
            & (busy_rows["end"] >= service_start)
        ]
        assert len(in_busy_interval) >= 1


def test_happy_path_lifecycle_without_queue_or_contingency(tmp_path):
    cfg = ScenarioConfig("S1_normal", seed=1010, duration_sec=120)
    cfg.output_root = tmp_path
    cfg.distributions.interarrival_mean_sec = 10_000.0  # single arrival in short run
    cfg.distributions.failure_rate_per_hour = 0.0
    cfg.distributions.maintenance_rate_per_hour = 0.0
    cfg.distributions.cashout_rate_per_hour = 0.0
    cfg.distributions.abandonment_base_probability = 0.0
    cfg.distributions.abandonment_threshold_sec = 999_999

    result = run_scenario(cfg)
    customer = pd.read_csv(result.customer_log)

    assert len(customer) == 1
    row = customer.iloc[0]
    assert row["served_flag"] == True
    assert row["abandoned"] == False
    assert pd.notna(row["arrival_ts"])
    assert pd.notna(row["service_start_ts"])
    assert pd.notna(row["service_end_ts"])
    assert int(row["waiting_time_sec"]) == 0


def test_priority_exceptional_dispatch_over_mixed_queue(monkeypatch):
    env = simpy.Environment()
    state = SimulationState(
        branch_id="PUNO-CENTRAL",
        atms={1: ATM(atm_id=1, state=ATMState.IDLE, cash_available=1000)},
    )

    c1 = Customer("CUST-00001", arrival_ts=0, transaction_type="retiro", priority_queue_flag=False)
    c2 = Customer("CUST-00002", arrival_ts=0, transaction_type="retiro", priority_queue_flag=True)
    state.enqueue(c1)
    state.enqueue(c2)

    dispatched: list[str] = []

    def fake_service(env, ctx, customer, atm_id):
        dispatched.append(customer.customer_id)
        yield env.timeout(0)

    from atm_simulator.processes import customer_flow as flow_module

    monkeypatch.setattr(flow_module, "service_customer", fake_service)

    ctx = {
        "config": ScenarioConfig("test", seed=1, duration_sec=2),
        "state": state,
        "event_bus": EventBus(),
    }

    env.process(customer_flow_process(env, ctx))
    env.run(until=2)

    assert len(dispatched) >= 1
    assert dispatched[0] == "CUST-00002"


def test_failure_interrupts_busy_atm_with_trace_consistency(tmp_path):
    cfg = ScenarioConfig("S5_falla_1_atm", seed=1111, duration_sec=900, total_atm=1)
    cfg.output_root = tmp_path
    cfg.distributions.interarrival_mean_sec = 10_000.0
    cfg.distributions.service_mean_sec = 900.0
    cfg.distributions.abandonment_base_probability = 0.0
    cfg.distributions.failure_rate_per_hour = 0.0  # isolate forced failure path
    cfg.distributions.maintenance_rate_per_hour = 0.0
    cfg.distributions.cashout_rate_per_hour = 0.0

    result = run_scenario(cfg)
    customer = pd.read_csv(result.customer_log)
    atm = pd.read_csv(result.atm_log)
    snapshot = pd.read_csv(result.snapshot_log)

    # customer in service must be interrupted by forced failure in S5
    assert (customer["abandon_reason"] == "falla_percibida").any()
    interrupted = customer[customer["abandon_reason"] == "falla_percibida"].iloc[0]
    assert interrupted["served_flag"] == False
    assert interrupted["abandoned"] == True

    # ATM trace must contain down_failure transition
    assert (atm["atm_state"] == "down_failure").any()

    # snapshots must reflect failure capacity effect
    assert (snapshot["failed_atm_count"] > 0).any()
