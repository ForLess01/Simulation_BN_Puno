from atm_simulator.runner import run_scenario
from atm_simulator.scenarios import scenario_matrix


def test_replay_same_seed_same_event_hash(tmp_path):
    cfg1 = scenario_matrix(seed=99)["S1_normal"]
    cfg2 = scenario_matrix(seed=99)["S1_normal"]
    cfg1.output_root = tmp_path / "run1"
    cfg2.output_root = tmp_path / "run2"
    r1 = run_scenario(cfg1)
    r2 = run_scenario(cfg2)
    assert r1.event_hash == r2.event_hash
