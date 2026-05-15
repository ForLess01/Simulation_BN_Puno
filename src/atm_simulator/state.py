from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .domain import ATM, ATMState, Customer


@dataclass(slots=True)
class SimulationState:
    branch_id: str
    atms: dict[int, ATM]
    queue: deque[Customer] = field(default_factory=deque)
    customers: dict[str, Customer] = field(default_factory=dict)
    blocked_arrivals_count: int = 0

    def enqueue(self, customer: Customer) -> None:
        customer.queue_entered = True
        customer.queue_position_at_arrival = len(self.queue) + 1
        self.queue.append(customer)

    def dequeue(self) -> Customer | None:
        if not self.queue:
            return None
        return self.queue.popleft()

    def effective_capacity(self) -> int:
        return sum(1 for atm in self.atms.values() if atm.state in {ATMState.IDLE, ATMState.BUSY})

    def counts(self) -> dict[str, int]:
        busy = sum(1 for a in self.atms.values() if a.state == ATMState.BUSY)
        idle = sum(1 for a in self.atms.values() if a.state == ATMState.IDLE)
        failed = sum(1 for a in self.atms.values() if a.state == ATMState.DOWN_FAILURE)
        cashout = sum(1 for a in self.atms.values() if a.state == ATMState.CASHOUT)
        maintenance = sum(1 for a in self.atms.values() if a.state == ATMState.DOWN_MAINTENANCE)
        return {
            "active_atm_count": busy + idle,
            "busy_atm_count": busy,
            "idle_atm_count": idle,
            "failed_atm_count": failed,
            "cashout_atm_count": cashout,
            "maintenance_atm_count": maintenance,
        }
