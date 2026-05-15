from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import simpy

from .config import ScenarioConfig
from .domain import ATM
from .io import CsvLogWriter
from .kpi import compute_kpis
from .processes.abandonment import abandonment_process
from .processes.arrivals import arrivals_process
from .processes.contingencies import contingencies_process
from .processes.customer_flow import customer_flow_process
from .processes.snapshots import snapshot_process
from .random import RandomEngine
from .scenarios import scenario_matrix
from .state import SimulationState
from .tracing import EventBus


@dataclass(slots=True)
class RunResult:
    scenario_id: str
    output_dir: Path
    customer_log: Path
    atm_log: Path
    snapshot_log: Path
    kpi_path: Path
    event_hash: str


def run_scenario(config: ScenarioConfig) -> RunResult:
    env = simpy.Environment()
    rng = RandomEngine(config.seed)
    atms = {i: ATM(atm_id=i) for i in range(1, config.total_atm + 1)}
    state = SimulationState(branch_id=config.branch_id, atms=atms)
    event_bus = EventBus()
    pressure = {"composite": "normal"}

    def is_restricted_window(sim_seconds: float) -> bool:
        base = datetime.strptime(config.base_timestamp, "%Y-%m-%d %H:%M:%S")
        hour = (base.hour + int(sim_seconds // 3600)) % 24
        return hour >= config.restricted_window_start_hour or hour < config.restricted_window_end_hour

    def priority_profile_sampler() -> bool:
        if config.scenario_id == "S4_pension65_atm":
            return rng.bernoulli(0.35)
        if config.scenario_id == "S9_critico":
            return rng.bernoulli(0.2)
        return rng.bernoulli(0.08)

    writer = CsvLogWriter(
        config.output_root / config.scenario_id / f"seed{config.seed}",
        datetime.strptime(config.base_timestamp, "%Y-%m-%d %H:%M:%S"),
        {
            "branch_id": config.branch_id,
            "payroll_cycle_type": config.payroll_cycle_type,
            "social_transfer_program": config.social_transfer_program,
            "social_transfer_access_channel": config.social_transfer_access_channel,
            "duration_sec": config.duration_sec,
            "scenario_id": config.scenario_id,
        },
    )
    event_bus.subscribe(writer.on_event)

    ctx = {
        "config": config,
        "rng": rng,
        "state": state,
        "event_bus": event_bus,
        "pressure": pressure,
        "is_restricted_window": is_restricted_window,
        "priority_profile_sampler": priority_profile_sampler,
    }
    env.process(arrivals_process(env, ctx))
    env.process(customer_flow_process(env, ctx))
    env.process(abandonment_process(env, ctx))
    env.process(contingencies_process(env, ctx))
    env.process(snapshot_process(env, ctx))
    env.run(until=config.duration_sec)

    output_dir = config.output_root / config.scenario_id / f"seed{config.seed}"
    logs = writer.flush_from_state(state, config.duration_sec)

    kpi_df = compute_kpis(logs["customer"], logs["atm"], logs["snapshot"])
    kpi_path = output_dir / "kpis.csv"
    kpi_df.to_csv(kpi_path, index=False)

    digest = hashlib.sha256()
    for ev in event_bus.events:
        digest.update(f"{ev.event_type}|{int(ev.ts)}|{ev.entity_id}".encode())

    return RunResult(config.scenario_id, output_dir, logs["customer"], logs["atm"], logs["snapshot"], kpi_path, digest.hexdigest())


def run_scenario_matrix(seed: int = 42) -> list[RunResult]:
    return [run_scenario(cfg) for cfg in scenario_matrix(seed).values()]
