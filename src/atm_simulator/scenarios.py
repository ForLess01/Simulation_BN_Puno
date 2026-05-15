from __future__ import annotations

from .config import DistributionConfig, ScenarioConfig


def scenario_matrix(seed: int = 42) -> dict[str, ScenarioConfig]:
    base = dict(seed=seed, distributions=DistributionConfig())
    return {
        "S1_normal": ScenarioConfig("S1_normal", payroll_cycle_type="ninguno", pressure_lambda_multiplier=1.0, **base),
        "S2_fin_mes": ScenarioConfig("S2_fin_mes", payroll_cycle_type="fin_mes", pressure_lambda_multiplier=1.5, **base),
        "S3_quincena": ScenarioConfig("S3_quincena", payroll_cycle_type="quincena", pressure_lambda_multiplier=1.3, **base),
        "S4_pension65_atm": ScenarioConfig("S4_pension65_atm", social_transfer_program="pension65", pressure_lambda_multiplier=1.25, **base),
        "S5_falla_1_atm": ScenarioConfig("S5_falla_1_atm", pressure_lambda_multiplier=1.2, contingency_overrides={"failure": 2.5}, **base),
        "S6_cashout": ScenarioConfig("S6_cashout", pressure_lambda_multiplier=1.25, contingency_overrides={"cashout": 2.5}, **base),
        "S7_mantenimiento": ScenarioConfig("S7_mantenimiento", pressure_lambda_multiplier=1.15, contingency_overrides={"maintenance": 2.5}, **base),
        "S8_nocturno_restringido": ScenarioConfig("S8_nocturno_restringido", duration_sec=6 * 3600, base_timestamp="2026-05-04 22:00:00", pressure_lambda_multiplier=0.8, **base),
        "S9_critico": ScenarioConfig("S9_critico", payroll_cycle_type="fin_mes", pressure_lambda_multiplier=2.0, contingency_overrides={"failure": 2.0, "cashout": 1.7, "maintenance": 1.7}, **base),
    }
