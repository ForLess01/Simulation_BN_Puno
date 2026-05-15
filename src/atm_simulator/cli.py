from __future__ import annotations

import argparse

from .runner import run_scenario, run_scenario_matrix
from .scenarios import scenario_matrix


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ATM SimPy simulator")
    parser.add_argument("--scenario", type=str, default="all")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.scenario == "all":
        results = run_scenario_matrix(args.seed)
        print(f"Ran {len(results)} scenarios")
        return

    scenarios = scenario_matrix(args.seed)
    result = run_scenario(scenarios[args.scenario])
    print(f"Scenario={result.scenario_id} output={result.output_dir} hash={result.event_hash}")
