from __future__ import annotations

import random

from .config import ScenarioConfig


class RandomEngine:
    def __init__(self, seed: int):
        self._rng = random.Random(seed)

    def exp(self, mean: float) -> float:
        return self._rng.expovariate(1.0 / mean)

    def bernoulli(self, p: float) -> bool:
        return self._rng.random() < p

    def choice(self, items: list[str]) -> str:
        return self._rng.choice(items)

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)


def interarrival_sampler(cfg: ScenarioConfig, rng: RandomEngine) -> float:
    mean = cfg.distributions.interarrival_mean_sec / max(cfg.pressure_lambda_multiplier, 0.1)
    return max(1.0, rng.exp(mean))


def service_sampler(cfg: ScenarioConfig, rng: RandomEngine, transaction_type: str) -> float:
    base = cfg.distributions.service_mean_sec
    multiplier = {
        "consulta": 0.7,
        "retiro": 1.0,
        "pago": 1.5,
        "transferencia": 1.3,
        "otros": 1.1,
    }.get(transaction_type, 1.0)
    return max(10.0, rng.exp(base * multiplier))


def should_abandon(waiting_sec: float, cfg: ScenarioConfig, rng: RandomEngine, pressure_level: str) -> bool:
    threshold = cfg.distributions.abandonment_threshold_sec
    base = cfg.distributions.abandonment_base_probability
    pressure_boost = {"normal": 0.0, "moderado": 0.04, "alto": 0.08, "critico": 0.15}.get(pressure_level, 0.0)
    if waiting_sec >= threshold:
        return True
    return rng.bernoulli(base + pressure_boost)
