from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable


CUSTOMER_LOG_FIELDS = [
    "event_id", "customer_id", "branch_id", "observation_date", "day_of_week", "day_type", "hour_block",
    "peak_flag", "peak_intraday_band", "peak_intraday_flag", "peak_payroll_flag", "social_transfer_program",
    "social_transfer_access_channel", "assisted_service_flag", "priority_queue_flag", "adulto_mayor_segment",
    "payroll_cycle_type", "peak_social_transfer_flag", "peak_operational_type", "peak_composite_level", "arrival_ts",
    "arrival_second_of_day", "arrival_minute_of_day", "interarrival_time_sec", "service_start_ts", "service_end_ts",
    "departure_ts", "waiting_time_sec", "service_time_sec", "time_in_system_sec", "queue_delay_flag", "loss_flag",
    "observed_sex", "estimated_age_range", "estimated_age_min", "estimated_age_max", "transaction_type",
    "transaction_type_inferred", "transaction_type_confidence", "atm_id", "queue_entered", "queue_position_at_arrival",
    "abandoned", "abandon_ts", "abandon_reason", "served_flag", "blocked_by_closed_hours", "observation_mode",
    "data_quality_flag",
]

ATM_LOG_FIELDS = [
    "atm_state_event_id", "atm_id", "state_start_ts", "state_end_ts", "atm_state", "cash_available", "failure_flag",
    "failure_type", "maintenance_flag", "maintenance_type", "network_outage_flag", "data_quality_flag",
]

SNAPSHOT_LOG_FIELDS = [
    "snapshot_id", "snapshot_ts", "snapshot_minute_of_day", "branch_id", "hour_block", "peak_flag", "peak_intraday_band",
    "peak_intraday_flag", "peak_payroll_flag", "social_transfer_program", "social_transfer_access_channel",
    "peak_operational_flag", "payroll_cycle_type", "peak_social_transfer_flag", "peak_operational_type",
    "peak_composite_level", "restricted_cash_window_flag", "queue_length_total", "active_atm_count", "busy_atm_count",
    "idle_atm_count", "failed_atm_count", "cashout_atm_count", "blocked_arrivals_count", "data_quality_flag",
]


def sim_time_to_str(base: datetime, sec: float) -> str:
    return (base + timedelta(seconds=int(sec))).strftime("%Y-%m-%d %H:%M:%S")


@dataclass(slots=True)
class Event:
    event_type: str
    ts: float
    entity_id: str
    before: dict[str, Any]
    after: dict[str, Any]
    payload: dict[str, Any]


class EventBus:
    def __init__(self):
        self._listeners: list[Callable[[Event], None]] = []
        self.events: list[Event] = []

    def subscribe(self, listener: Callable[[Event], None]) -> None:
        self._listeners.append(listener)

    def emit(self, event: Event) -> None:
        self.events.append(event)
        for listener in self._listeners:
            listener(event)
