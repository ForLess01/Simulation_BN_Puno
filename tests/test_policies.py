from atm_simulator.domain import ATM, ATMState
from atm_simulator.policies import select_available_atm
from atm_simulator.state import SimulationState


def test_select_available_atm_skips_non_idle_states():
    state = SimulationState(
        branch_id="PUNO-CENTRAL",
        atms={
            1: ATM(1, state=ATMState.DOWN_FAILURE),
            2: ATM(2, state=ATMState.CASHOUT, cash_available=0),
            3: ATM(3, state=ATMState.IDLE, cash_available=1000),
        },
    )
    assert select_available_atm(state) == 3
