import pandas as pd

from atm_simulator.kpi import compute_kpis
from atm_simulator.runner import run_scenario
from atm_simulator.scenarios import scenario_matrix


def test_s4_and_s6_are_behaviorally_different(tmp_path):
    scenarios = scenario_matrix(seed=101)
    s4 = scenarios["S4_pension65_atm"]
    s6 = scenarios["S6_cashout"]
    s4.output_root = tmp_path / "s4"
    s6.output_root = tmp_path / "s6"

    r4 = run_scenario(s4)
    r6 = run_scenario(s6)
    assert r4.event_hash != r6.event_hash

    c4 = pd.read_csv(r4.customer_log)
    c6 = pd.read_csv(r6.customer_log)
    assert c4["priority_queue_flag"].mean() > c6["priority_queue_flag"].mean()


def test_s8_restricted_window_blocks_arrivals(tmp_path):
    cfg = scenario_matrix(seed=202)["S8_nocturno_restringido"]
    cfg.output_root = tmp_path
    result = run_scenario(cfg)
    customer = pd.read_csv(result.customer_log)
    snapshot = pd.read_csv(result.snapshot_log)

    assert (customer["blocked_by_closed_hours"] == True).any()
    assert (snapshot["restricted_cash_window_flag"] == True).any()


def test_s5_has_forced_failure_and_s7_has_forced_maintenance(tmp_path):
    scenarios = scenario_matrix(seed=303)
    s5 = scenarios["S5_falla_1_atm"]
    s7 = scenarios["S7_mantenimiento"]
    s5.output_root = tmp_path / "s5"
    s7.output_root = tmp_path / "s7"

    r5 = run_scenario(s5)
    r7 = run_scenario(s7)
    atm5 = pd.read_csv(r5.atm_log)
    atm7 = pd.read_csv(r7.atm_log)

    assert (atm5["atm_state"] == "down_failure").any()
    assert (atm7["atm_state"] == "down_maintenance").any()


def test_s9_has_multicausal_events(tmp_path):
    s9 = scenario_matrix(seed=404)["S9_critico"]
    s9.output_root = tmp_path / "s9"
    r9 = run_scenario(s9)
    atm = pd.read_csv(r9.atm_log)

    states = set(atm["atm_state"].unique())
    assert "down_failure" in states
    assert "cashout" in states
    assert "down_maintenance" in states


def test_kpi_recomputation_from_logs_is_stable(tmp_path):
    cfg = scenario_matrix(seed=505)["S1_normal"]
    cfg.output_root = tmp_path / "kpi"
    r = run_scenario(cfg)
    k1 = compute_kpis(r.customer_log, r.atm_log, r.snapshot_log)
    k2 = compute_kpis(r.customer_log, r.atm_log, r.snapshot_log)
    assert k1.equals(k2)
