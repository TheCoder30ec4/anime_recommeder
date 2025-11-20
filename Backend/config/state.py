from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional


class SessionStateStore:
    """In-memory store for chat session state."""

    def __init__(self) -> None:
        self._states: Dict[str, Dict[str, Any]] = {}

    def get_state(self, session_id: str) -> Dict[str, Any]:
        state = self._states.get(session_id)
        return deepcopy(state) if state else {}

    def set_state(self, session_id: str, state: Dict[str, Any]) -> None:
        self._states[session_id] = deepcopy(state)

    def clear_state(self, session_id: str) -> None:
        self._states.pop(session_id, None)

    def reset(self) -> None:
        self._states.clear()


session_state_store = SessionStateStore()
