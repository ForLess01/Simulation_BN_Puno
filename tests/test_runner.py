from atm_simulator.runner import run_scenario
from atm_simulator.scenarios import scenario_matrix
import pandas as pd


def test_s1_run_produces_three_logs(tmp_path):
    cfg = scenario_matrix(seed=77)["S1_normal"]
    cfg.output_root = tmp_path
    result = run_scenario(cfg)
    assert result.customer_log.exists()
    assert result.atm_log.exists()
    assert result.snapshot_log.exists()


def test_logs_have_derived_columns_and_atm_transitions(tmp_path):
    cfg = scenario_matrix(seed=77)["S1_normal"]
    cfg.output_root = tmp_path
    result = run_scenario(cfg)
    customer = pd.read_csv(result.customer_log)
    atm = pd.read_csv(result.atm_log)
    snapshot = pd.read_csv(result.snapshot_log)

    assert customer["interarrival_time_sec"].sum() > 0
    assert customer["arrival_second_of_day"].max() > 0
    assert customer["arrival_minute_of_day"].max() > 0
    assert customer["hour_block"].nunique() >= 2
    assert snapshot["restricted_cash_window_flag"].isin([True, False]).all()
    assert len(atm) > cfg.total_atm
    assert atm["state_end_ts"].astype(str).str.len().min() > 0
