from dataclasses import dataclass
from core.exceptions import SafetyBlockError


@dataclass
class SafetyState:
    emergency_stop: bool = False
    emergency_reason: str = ""


_safety_state = SafetyState()


def get_safety_state() -> SafetyState:
    return _safety_state


def assert_execution_allowed(operating_mode: str, account_mode: str, allow_demo: bool) -> None:
    """Enforce monitoring default and block real-account execution."""
    if _safety_state.emergency_stop:
        raise SafetyBlockError(f"Emergency stop active: {_safety_state.emergency_reason}")
    if operating_mode.upper() == "MONITORING":
        raise SafetyBlockError("System is in MONITORING mode. Automated order execution is disabled.")
    if account_mode.upper() == "REAL":
        raise SafetyBlockError("Real-account automated execution is blocked in this version.")
    if not allow_demo:
        raise SafetyBlockError("Demo trading requires explicit ALLOW_DEMO_TRADING=true configuration.")
