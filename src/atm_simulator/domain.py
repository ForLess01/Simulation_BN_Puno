from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ATMState(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    CASHOUT = "cashout"
    DOWN_MAINTENANCE = "down_maintenance"
    DOWN_FAILURE = "down_failure"
    OFFLINE = "offline"


class EventType(str, Enum):
    CUSTOMER_ARRIVAL = "customer_arrival"
    QUEUE_ENTER = "queue_enter"
    SERVICE_START = "service_start"
    SERVICE_END = "service_end"
    CUSTOMER_ABANDON = "customer_abandon"
    ATM_FAILURE = "atm_failure"
    ATM_CASHOUT = "atm_cashout"
    ATM_MAINTENANCE_START = "atm_maintenance_start"
    ATM_RECOVERY = "atm_recovery"
    CASH_REPLENISHMENT = "cash_replenishment"
    SYSTEM_SNAPSHOT = "system_snapshot"


STATE_PRECEDENCE = {
    ATMState.DOWN_FAILURE: 5,
    ATMState.DOWN_MAINTENANCE: 4,
    ATMState.CASHOUT: 3,
    ATMState.BUSY: 2,
    ATMState.IDLE: 1,
    ATMState.OFFLINE: 0,
}


@dataclass(slots=True)
class Customer:
    customer_id: str
    arrival_ts: float
    transaction_type: str
    queue_entered: bool = False
    queue_position_at_arrival: int = 0
    service_start_ts: float | None = None
    service_end_ts: float | None = None
    departure_ts: float | None = None
    abandoned: bool = False
    abandon_ts: float | None = None
    abandon_reason: str | None = None
    served_flag: bool = False
    atm_id: int | None = None
    interarrival_time_sec: float = 0.0
    priority_queue_flag: bool = False
    blocked_by_closed_hours: bool = False
    adulto_mayor_segment: str = ""


@dataclass(slots=True)
class ATM:
    atm_id: int
    state: ATMState = ATMState.IDLE
    cash_available: float = 25000.0
    failure_flag: bool = False
    failure_type: str | None = None
    maintenance_flag: bool = False
    maintenance_type: str | None = None
    network_outage_flag: bool = False
    current_customer_id: str | None = None

    @property
    def is_operable(self) -> bool:
        return self.state in {ATMState.IDLE, ATMState.BUSY}
