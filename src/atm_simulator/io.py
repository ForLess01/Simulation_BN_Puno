from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from datetime import timedelta
from typing import Any

from .tracing import ATM_LOG_FIELDS, CUSTOMER_LOG_FIELDS, SNAPSHOT_LOG_FIELDS, Event, sim_time_to_str


class CsvLogWriter:
    def __init__(self, output_dir: Path, base_dt: datetime, context: dict):
        self.output_dir = output_dir
        self.base_dt = base_dt
        self.ctx = context
        self.customer_rows: list[dict] = []
        self.atm_rows: list[dict] = []
        self.snapshot_rows: list[dict] = []
        self.customer_index: dict[str, dict] = {}
        self.last_atm_state: dict[int, dict] = {}
        self.atm_seq = 0
        self.customer_seq = 0

    def _base_dimensions(self, ts: float) -> dict:
        dt = self.base_dt + timedelta(seconds=int(ts))
        minute_of_day = dt.hour * 60 + dt.minute
        hour_block = f"{dt.hour:02d}:00-{dt.hour:02d}:59"
        payroll = self.ctx["payroll_cycle_type"]
        peak_intraday_band = "morning_transition"
        if 11 <= dt.hour <= 13:
            peak_intraday_band = "midday_peak"
        elif 14 <= dt.hour <= 16:
            peak_intraday_band = "afternoon_peak"
        elif 17 <= dt.hour <= 19:
            peak_intraday_band = "evening_peak"
        elif dt.hour >= 20 or dt.hour <= 6:
            peak_intraday_band = "night_low"
        peak_intraday_flag = peak_intraday_band in {"midday_peak", "afternoon_peak", "evening_peak"}
        peak_payroll_flag = payroll in {"inicio_mes", "quincena", "fin_mes"}
        peak_social_transfer_flag = self.ctx["social_transfer_program"] != "ninguno"
        restricted_window = dt.hour >= 22 or dt.hour < 5
        return {
            "observation_date": dt.strftime("%Y-%m-%d"),
            "day_of_week": dt.strftime("%A").lower(),
            "day_type": "weekday",
            "hour_block": hour_block,
            "arrival_second_of_day": dt.hour * 3600 + dt.minute * 60 + dt.second,
            "arrival_minute_of_day": minute_of_day,
            "peak_intraday_band": peak_intraday_band,
            "peak_intraday_flag": peak_intraday_flag,
            "peak_payroll_flag": peak_payroll_flag,
            "peak_social_transfer_flag": peak_social_transfer_flag,
            "restricted_cash_window_flag": restricted_window,
        }

    def on_event(self, event: Event) -> None:
        if event.event_type == "customer_arrival":
            self._on_customer_arrival(event)
        if event.event_type == "service_start":
            self._on_service_start(event)
        if event.event_type in {"service_end", "atm_cashout"}:
            self._on_service_end(event)
        if event.event_type == "customer_abandon":
            self._on_customer_abandon(event)
        if event.event_type in {"atm_failure", "atm_maintenance_start", "atm_recovery", "atm_cashout", "cash_replenishment", "service_start", "service_end"}:
            self._on_atm_transition(event)
        if event.event_type == "system_snapshot":
            self.snapshot_rows.append(self._snapshot_row(event))

    def flush_from_state(self, state, duration_sec: float) -> dict[str, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        customer_path = self.output_dir / "customer_event_log.csv"
        atm_path = self.output_dir / "atm_state_log.csv"
        snapshot_path = self.output_dir / "system_snapshot_log.csv"

        for customer_id in sorted(self.customer_index.keys()):
            row = self.customer_index[customer_id]
            self.customer_rows.append({k: row.get(k, "") for k in CUSTOMER_LOG_FIELDS})
        for atm_id, open_state in list(self.last_atm_state.items()):
            open_state["state_end_ts"] = sim_time_to_str(self.base_dt, duration_sec)
            self.atm_rows.append(open_state)
            del self.last_atm_state[atm_id]

        self._write(customer_path, CUSTOMER_LOG_FIELDS, self.customer_rows)
        self._write(atm_path, ATM_LOG_FIELDS, self.atm_rows)
        self._write(snapshot_path, SNAPSHOT_LOG_FIELDS, self.snapshot_rows)
        return {"customer": customer_path, "atm": atm_path, "snapshot": snapshot_path}

    def _write(self, path: Path, fields: list[str], rows: list[dict]):
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            normalized = [self._normalize_row_for_csv(row) for row in rows]
            writer.writerows(normalized)

    def _normalize_row_for_csv(self, row: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, bool):
                normalized[key] = "true" if value else "false"
            else:
                normalized[key] = value
        return normalized

    def _create_customer_row(self, customer_id: str, ts: float, payload: dict) -> dict:
        self.customer_seq += 1
        base = self._base_dimensions(ts)
        arrival_str = sim_time_to_str(self.base_dt, ts)
        return {
            "event_id": f"EVT-{self.customer_seq:05d}",
            "customer_id": customer_id,
            "branch_id": self.ctx["branch_id"],
            "observation_date": base["observation_date"],
            "day_of_week": base["day_of_week"],
            "day_type": base["day_type"],
            "hour_block": base["hour_block"],
            "peak_flag": False,
            "peak_intraday_band": base["peak_intraday_band"],
            "peak_intraday_flag": base["peak_intraday_flag"],
            "peak_payroll_flag": base["peak_payroll_flag"],
            "social_transfer_program": self.ctx["social_transfer_program"],
            "social_transfer_access_channel": self.ctx["social_transfer_access_channel"],
            "assisted_service_flag": False,
            "priority_queue_flag": payload.get("priority_queue_flag", False),
            "adulto_mayor_segment": payload.get("adulto_mayor_segment", ""),
            "payroll_cycle_type": self.ctx["payroll_cycle_type"],
            "peak_social_transfer_flag": base["peak_social_transfer_flag"],
            "peak_operational_type": "none",
            "peak_composite_level": "normal",
            "arrival_ts": arrival_str,
            "arrival_second_of_day": base["arrival_second_of_day"],
            "arrival_minute_of_day": base["arrival_minute_of_day"],
            "interarrival_time_sec": int(payload.get("interarrival_time_sec", 0)),
            "service_start_ts": "",
            "service_end_ts": "",
            "departure_ts": "",
            "waiting_time_sec": 0,
            "service_time_sec": 0,
            "time_in_system_sec": 0,
            "queue_delay_flag": False,
            "loss_flag": False,
            "observed_sex": "no_determinado",
            "estimated_age_range": "adulto",
            "estimated_age_min": 30,
            "estimated_age_max": 59,
            "transaction_type": payload.get("transaction_type", "otros"),
            "transaction_type_inferred": True,
            "transaction_type_confidence": "media",
            "atm_id": "",
            "queue_entered": not payload.get("blocked_by_closed_hours", False),
            "queue_position_at_arrival": int(payload.get("queue_position_at_arrival", 0)),
            "abandoned": False,
            "abandon_ts": "",
            "abandon_reason": "",
            "served_flag": False,
            "blocked_by_closed_hours": payload.get("blocked_by_closed_hours", False),
            "observation_mode": "externa_visual",
            "data_quality_flag": "estimado",
            "_arrival_ts_sec": float(ts),
            "_service_start_sec": None,
        }

    def _on_customer_arrival(self, event: Event) -> None:
        customer_id = event.entity_id
        row = self.customer_index.get(customer_id)
        if row is None:
            row = self._create_customer_row(customer_id, event.ts, event.payload)
            self.customer_index[customer_id] = row
        if event.payload.get("blocked_by_closed_hours", False):
            row["abandoned"] = True
            row["loss_flag"] = True
            row["abandon_reason"] = "horario"
            row["abandon_ts"] = sim_time_to_str(self.base_dt, event.ts)
            row["departure_ts"] = sim_time_to_str(self.base_dt, event.ts)
            row["time_in_system_sec"] = 0
            row["served_flag"] = False

    def _on_service_start(self, event: Event) -> None:
        row = self.customer_index.get(event.entity_id)
        if row is None:
            return
        row["service_start_ts"] = sim_time_to_str(self.base_dt, event.ts)
        row["_service_start_sec"] = float(event.ts)
        row["waiting_time_sec"] = max(0, int(event.ts - row["_arrival_ts_sec"]))
        row["queue_delay_flag"] = row["waiting_time_sec"] > 0
        row["atm_id"] = event.payload.get("atm_id", "")

    def _on_service_end(self, event: Event) -> None:
        row = self.customer_index.get(event.entity_id)
        if row is None:
            return
        row["service_end_ts"] = sim_time_to_str(self.base_dt, event.ts)
        row["departure_ts"] = sim_time_to_str(self.base_dt, event.ts)
        start = row.get("_service_start_sec")
        if start is not None:
            row["service_time_sec"] = max(0, int(event.ts - start))
        row["time_in_system_sec"] = max(0, int(event.ts - row["_arrival_ts_sec"]))
        row["served_flag"] = bool(event.payload.get("served_flag", True))
        row["abandoned"] = bool(event.payload.get("abandoned", False))
        row["loss_flag"] = row["abandoned"]
        if event.event_type == "atm_cashout":
            row["peak_operational_type"] = "cashout"

    def _on_customer_abandon(self, event: Event) -> None:
        row = self.customer_index.get(event.entity_id)
        if row is None:
            return
        row["abandoned"] = True
        row["served_flag"] = False
        row["loss_flag"] = True
        row["abandon_reason"] = event.payload.get("reason", "saturacion")
        row["abandon_ts"] = sim_time_to_str(self.base_dt, event.ts)
        row["departure_ts"] = sim_time_to_str(self.base_dt, event.ts)
        row["time_in_system_sec"] = max(0, int(event.ts - row["_arrival_ts_sec"]))
        row["peak_operational_type"] = "atm_failure" if row["abandon_reason"] == "falla_percibida" else row["peak_operational_type"]

    def _on_atm_transition(self, event: Event) -> None:
        atm_id = event.payload.get("atm_id")
        if atm_id is None:
            return
        current_state = event.after.get("state") or event.after.get("atm_state")
        if current_state is None:
            return
        previous = self.last_atm_state.get(atm_id)
        if previous is not None:
            previous["state_end_ts"] = sim_time_to_str(self.base_dt, event.ts)
            self.atm_rows.append(previous)
        self.atm_seq += 1
        self.last_atm_state[atm_id] = {
            "atm_state_event_id": f"ATMSTATE-{self.atm_seq:05d}",
            "atm_id": atm_id,
            "state_start_ts": sim_time_to_str(self.base_dt, event.ts),
            "state_end_ts": "",
            "atm_state": current_state,
            "cash_available": round(float(event.payload.get("cash_available", 0.0)), 2),
            "failure_flag": current_state == "down_failure",
            "failure_type": "hardware" if current_state == "down_failure" else "",
            "maintenance_flag": current_state == "down_maintenance",
            "maintenance_type": "preventivo" if current_state == "down_maintenance" else "",
            "network_outage_flag": False,
            "data_quality_flag": "estimado",
        }

    def _snapshot_row(self, event: Event) -> dict:
        ts = sim_time_to_str(self.base_dt, event.ts)
        base = self._base_dimensions(event.ts)
        p = event.payload
        peak_operational_type = "none"
        if p["failed_atm_count"] > 0:
            peak_operational_type = "atm_failure"
        elif p["cashout_atm_count"] > 0:
            peak_operational_type = "cashout"
        peak_level = "normal"
        if p["queue_length_total"] >= 10 or p["failed_atm_count"] >= 2:
            peak_level = "critico"
        elif p["queue_length_total"] >= 6:
            peak_level = "alto"
        elif p["queue_length_total"] >= 3:
            peak_level = "moderado"
        return {
            "snapshot_id": f"SNAP-{len(self.snapshot_rows)+1:05d}", "snapshot_ts": ts, "snapshot_minute_of_day": int(event.ts // 60),
            "branch_id": self.ctx["branch_id"], "hour_block": base["hour_block"], "peak_flag": p["queue_length_total"] > 4,
            "peak_intraday_band": base["peak_intraday_band"], "peak_intraday_flag": base["peak_intraday_flag"], "peak_payroll_flag": base["peak_payroll_flag"],
            "social_transfer_program": self.ctx["social_transfer_program"], "social_transfer_access_channel": self.ctx["social_transfer_access_channel"],
            "peak_operational_flag": p["failed_atm_count"] > 0 or p["cashout_atm_count"] > 0, "payroll_cycle_type": self.ctx["payroll_cycle_type"],
            "peak_social_transfer_flag": base["peak_social_transfer_flag"], "peak_operational_type": peak_operational_type, "peak_composite_level": peak_level,
            "restricted_cash_window_flag": base["restricted_cash_window_flag"], "queue_length_total": p["queue_length_total"], "active_atm_count": p["active_atm_count"],
            "busy_atm_count": p["busy_atm_count"], "idle_atm_count": p["idle_atm_count"], "failed_atm_count": p["failed_atm_count"],
            "cashout_atm_count": p["cashout_atm_count"], "blocked_arrivals_count": p["blocked_arrivals_count"], "data_quality_flag": "estimado",
        }
