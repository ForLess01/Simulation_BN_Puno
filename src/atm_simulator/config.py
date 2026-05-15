from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


@dataclass(slots=True)
class DistributionConfig:
    interarrival_mean_sec: float = 25.0
    service_mean_sec: float = 90.0
    abandonment_threshold_sec: float = 330.0
    abandonment_base_probability: float = 0.03
    failure_rate_per_hour: float = 0.03
    maintenance_rate_per_hour: float = 0.02
    cashout_rate_per_hour: float = 0.02


@dataclass(slots=True)
class ScenarioConfig:
    scenario_id: str
    seed: int
    duration_sec: int = 12 * 3600
    branch_id: str = "PUNO-CENTRAL"
    total_atm: int = 4
    base_timestamp: str = "2026-05-04 08:00:00"
    snapshot_interval_sec: int = 60
    restricted_window_start_hour: int = 22
    restricted_window_end_hour: int = 5
    payroll_cycle_type: str = "ninguno"
    social_transfer_program: str = "ninguno"
    social_transfer_access_channel: str = "desconocido"
    pressure_lambda_multiplier: float = 1.0
    contingency_overrides: Mapping[str, float] = field(default_factory=dict)
    distributions: DistributionConfig = field(default_factory=DistributionConfig)
    output_root: Path = Path("outputs")
