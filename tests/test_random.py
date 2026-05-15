from atm_simulator.config import ScenarioConfig
from atm_simulator.random import RandomEngine, interarrival_sampler


def test_rng_reproducibility_interarrivals():
    cfg = ScenarioConfig("S1_normal", seed=123)
    rng1 = RandomEngine(123)
    rng2 = RandomEngine(123)
    s1 = [round(interarrival_sampler(cfg, rng1), 6) for _ in range(5)]
    s2 = [round(interarrival_sampler(cfg, rng2), 6) for _ in range(5)]
    assert s1 == s2
